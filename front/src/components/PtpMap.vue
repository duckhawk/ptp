<template>
  <div class="ptp-map">
    <header class="header">
      <h1 class="title">Закрытая карта ПТП</h1>
      <div class="auth">
        <!-- OIDC: состояние берётся из /api/auth/user/, вход через Keycloak -->
        <template v-if="user === null">
          <span class="auth-loading">Загрузка…</span>
        </template>
        <template v-else-if="user && user.is_authenticated">
          <span class="user">{{ user.display_name || user.username }}</span>
          <form action="/oidc/logout/" method="POST" class="logout-form">
            <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken">
            <button type="submit" class="btn btn-outline">Выйти</button>
          </form>
        </template>
        <template v-else>
          <a href="/oidc/authenticate/" class="btn btn-primary">Войти</a>
        </template>
      </div>
    </header>

    <div v-if="user === null" class="login-prompt">
      <p>Проверка авторизации…</p>
    </div>
    <div v-else-if="!user.is_authenticated" class="login-prompt">
      <p>Войдите чтобы работать с картой и зонами.</p>
    </div>
    <div v-else class="layout" :class="{ 'layout-panel-hidden': !panelVisible }">
      <aside class="panel">
        <div class="panel-header">
          <input
            v-show="panelVisible"
            v-model="coordSearchText"
            type="text"
            class="input coord-search"
            placeholder="Широта долгота (55.7558 37.6173)"
            title="Поиск по координатам"
            @keyup.enter="goToCoords"
          >
          <button
            type="button"
            class="btn btn-icon panel-toggle"
            :title="panelVisible ? 'Скрыть меню' : 'Показать меню'"
            :aria-label="panelVisible ? 'Скрыть меню' : 'Показать меню'"
            @click="panelVisible = !panelVisible"
          >
            {{ panelVisible ? '‹' : '›' }}
          </button>
        </div>
        <div class="panel-content">
        <section class="section section-zones">
          <h3>Существующие зоны</h3>
          <ul v-if="zones.length > 0" class="zones-list">
            <li
              v-for="zone in zones"
              :key="zone.id"
              class="zone-item"
              :class="{ 'zone-item--marked-for-deletion': zone.marked_for_deletion }"
              title="Перейти к зоне на карте"
              @click="focusMapOnZone(zone)"
            >
              <span class="zone-info">
                <strong>#{{ zone.id }}</strong> — {{ zone.date || '—' }}, {{ (zone.points || []).length }} точек
                <span v-if="zone.marked_for_deletion" class="zone-marked-deletion">
                  К удалению после {{ zone.delete_after || '—' }}
                </span>
                <span v-if="zone.notes" class="zone-notes">{{ zone.notes }}</span>
                <span class="zone-creator">Создатель: {{ zone.creator_display_name || (zone.creator_id ? '#' + zone.creator_id : '—') }}</span>
              </span>
              <span v-if="user.is_staff" class="zone-actions">
                <template v-if="zone.marked_for_deletion">
                  <button
                    type="button"
                    class="btn btn-small btn-outline"
                    title="Отменить удаление"
                    @click.stop="cancelDeletion(zone)"
                  >
                    Отмена
                  </button>
                </template>
                <template v-else>
                  <button
                    type="button"
                    class="btn btn-small btn-outline btn-danger"
                    title="Удалить зону сразу"
                    @click.stop="deleteImmediately(zone)"
                  >
                    Сейчас
                  </button>
                  <template v-if="deferredDeleteZoneId === zone.id">
                    <span class="deferred-delete-inline">
                      <input
                        v-model="deferredDeleteDate"
                        type="date"
                        class="input input-date-small"
                        title="Дата удаления"
                      >
                      <button
                        type="button"
                        class="btn btn-small btn-primary"
                        title="Пометить к удалению"
                        @click.stop="markForDeletion(zone)"
                      >
                        Пометить
                      </button>
                      <button
                        type="button"
                        class="btn btn-small btn-outline"
                        @click.stop="deferredDeleteZoneId = null"
                      >
                        ×
                      </button>
                    </span>
                  </template>
                  <button
                    v-else
                    type="button"
                    class="btn btn-small btn-outline"
                    title="Удалить после указанной даты"
                    @click.stop="openDeferredDelete(zone)"
                  >
                    После
                  </button>
                </template>
              </span>
            </li>
          </ul>
          <p v-else class="zones-empty">Зон пока нет.</p>
        </section>
        <section v-if="user.is_staff" class="section">
          <h3>Добавить зону (ввод точек построчно)</h3>
          <p class="hint">Клик по карте добавляет точку в поле ниже. Или вводите вручную: одна точка на строку — широта пробел долгота (например: 55.7558 37.6173).</p>
          <textarea
            v-model="pointsText"
            class="textarea"
            rows="6"
            placeholder="55.7558 37.6173&#10;55.7512 37.6185&#10;55.7520 37.6200"
          />
          <label class="label">
            Примечания
            <textarea v-model="zoneNotes" class="textarea textarea-notes" rows="2" placeholder="Необязательно"></textarea>
          </label>
          <label class="label">
            Дата закладки
            <input v-model="zoneDate" type="date" class="input">
          </label>
          <button
            type="button"
            class="btn btn-primary btn-block"
            :disabled="!canSaveZone"
            @click="saveZone"
          >
            Сохранить зону
          </button>
        </section>
        <button
          type="button"
          class="btn btn-secondary btn-block"
          :disabled="zones.length === 0"
          @click="exportCsv"
        >
          Экспорт в Excel (CSV)
        </button>
        </div>
      </aside>
      <div class="map-container">
        <div ref="mapContainer" class="map-container-inner"></div>
      </div>
    </div>
  </div>
</template>

<script>
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import OSM from 'ol/source/OSM'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Polygon from 'ol/geom/Polygon'
import Point from 'ol/geom/Point'
import { fromLonLat, toLonLat } from 'ol/proj'
import Style from 'ol/style/Style'
import Fill from 'ol/style/Fill'
import Stroke from 'ol/style/Stroke'
import Circle from 'ol/style/Circle'
import Text from 'ol/style/Text'
import 'ol/ol.css'

const API_ZONES = '/api/zones/'
const API_AUTH_USER = '/api/auth/user/'

function getCsrfToken() {
  const name = 'csrftoken'
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? match[2] : null
}

function parsePoints(text) {
  if (!text || !text.trim()) return []
  const lines = text.trim().split(/\r?\n/)
  const points = []
  for (const line of lines) {
    const parts = line.trim().replace(/,/g, ' ').split(/\s+/)
    if (parts.length >= 2) {
      const lat = parseFloat(parts[0])
      const lng = parseFloat(parts[1])
      if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
        points.push([lat, lng])
      }
    }
  }
  return points
}

export default {
  name: 'PtpMap',
  data() {
    return {
      map: null,
      zonesVectorSource: null,
      searchMarkerSource: null,
      user: null,
      pointsText: '',
      zoneDate: new Date().toISOString().slice(0, 10),
      zoneNotes: '',
      zones: [],
      panelVisible: true,
      coordSearchText: '',
      deferredDeleteZoneId: null,
      deferredDeleteDate: ''
    }
  },
  computed: {
    csrfToken() {
      const match = document.cookie.match(/csrftoken=([^;]+)/)
      return match ? match[1] : ''
    },
    canSaveZone() {
      const points = parsePoints(this.pointsText)
      return points.length >= 2 && this.zoneDate
    }
  },
  mounted() {
    // OIDC: получаем текущего пользователя из сессии Django (после /oidc/callback/)
    this.fetchUser().then(() => {
      if (this.user && this.user.is_authenticated) {
        this.fetchZones()
        // Карта рендерится только при user.is_authenticated — инициализируем после появления контейнера в DOM
        this.$nextTick(() => this.initMap())
      }
    })
  },
  beforeUnmount() {
    if (this.map) {
      this.map.setTarget(undefined)
      this.map = null
    }
  },
  methods: {
    goToCoords() {
      const text = (this.coordSearchText || '').trim().replace(/,/g, ' ')
      const parts = text.split(/\s+/).filter(Boolean)
      if (parts.length < 2) return
      const lat = parseFloat(parts[0])
      const lng = parseFloat(parts[1])
      if (Number.isNaN(lat) || Number.isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) return
      if (!this.map) return
      const center = fromLonLat([lng, lat])
      this.map.getView().animate({
        center,
        zoom: 14,
        duration: 300
      })
      // Показать маркер искомой точки
      if (this.searchMarkerSource) {
        this.searchMarkerSource.clear()
        this.searchMarkerSource.addFeature(new Feature(new Point(center)))
      }
    },
    focusMapOnZone(zone) {
      if (!this.map || !zone.points || zone.points.length < 2) return
      const coords = zone.points.map(([lat, lng]) => fromLonLat([lng, lat]))
      const xs = coords.map(c => c[0])
      const ys = coords.map(c => c[1])
      const extent = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
      this.map.getView().fit(extent, { padding: [40, 40, 40, 40], maxZoom: 15, duration: 300 })
    },
    initMap() {
      if (!this.$refs.mapContainer) return
      this.zonesVectorSource = new VectorSource()
      this.draftVectorSource = new VectorSource()
      const osmLayer = new TileLayer({ source: new OSM() })
      const zonesLayer = new VectorLayer({
        source: this.zonesVectorSource,
        style: (feature) => {
          const marked = feature.get('markedForDeletion')
          const zoneId = feature.get('zoneId')
          const zoneDate = feature.get('zoneDate')
          const zoneNotes = feature.get('zoneNotes')
          const geom = feature.getGeometry()
          const interior = geom.getType() === 'Polygon' ? geom.getInteriorPoint() : null
          const labelLines = []
          if (zoneId != null) labelLines.push(`#${zoneId}`)
          if (zoneDate) labelLines.push(zoneDate)
          if (zoneNotes) labelLines.push(zoneNotes.length > 25 ? zoneNotes.slice(0, 24) + '…' : zoneNotes)
          const labelText = labelLines.join(' · ')
          const baseFill = marked
            ? new Fill({ color: 'rgba(244, 67, 54, 0.15)' })
            : new Fill({ color: 'rgba(33, 150, 243, 0.2)' })
          const baseStroke = marked
            ? new Stroke({ color: '#f44336', width: 2, lineDash: [8, 4] })
            : new Stroke({ color: '#2196F3', width: 2 })
          const textStyle = interior && labelText
            ? new Text({
                text: labelText,
                fill: new Fill({ color: '#fff' }),
                stroke: new Stroke({ color: 'rgba(0,0,0,0.7)', width: 2 }),
                font: 'bold 13px sans-serif',
                overflow: true,
                geometry: interior
              })
            : null
          return new Style({
            fill: baseFill,
            stroke: baseStroke,
            text: textStyle || undefined
          })
        }
      })
      // Черновик новой зоны — оранжевый цвет, точки и контур
      const draftLayer = new VectorLayer({
        source: this.draftVectorSource,
        style: (feature) => {
          const geom = feature.getGeometry()
          if (geom.getType() === 'Point') {
            return new Style({
              image: new Circle({
                radius: 6,
                fill: new Fill({ color: 'rgba(255, 152, 0, 0.9)' }),
                stroke: new Stroke({ color: '#e65100', width: 2 })
              })
            })
          }
          return new Style({
            fill: new Fill({ color: 'rgba(255, 152, 0, 0.15)' }),
            stroke: new Stroke({ color: '#ff9800', width: 2 })
          })
        }
      })
      // Маркер точки поиска по координатам — яркая подсветка
      this.searchMarkerSource = new VectorSource()
      const searchMarkerLayer = new VectorLayer({
        source: this.searchMarkerSource,
        zIndex: 10,
        style: new Style({
          image: new Circle({
            radius: 12,
            fill: new Fill({ color: 'rgba(76, 175, 80, 0.9)' }),
            stroke: new Stroke({ color: '#fff', width: 3 })
          })
        })
      })
      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [osmLayer, zonesLayer, draftLayer, searchMarkerLayer],
        view: new View({
          center: fromLonLat([37.6173, 55.7558]),
          zoom: 10
        })
      })
      this.map.on('click', (evt) => this.onMapClick(evt))
      this.drawZones()
      this.drawDraft()
    },
    onMapClick(evt) {
      const lonLat = toLonLat(evt.coordinate)
      const lat = lonLat[1]
      const lng = lonLat[0]
      const line = (this.pointsText ? this.pointsText.trimEnd() + '\n' : '') + lat.toFixed(5) + ' ' + lng.toFixed(5)
      this.pointsText = line
    },
    drawDraft() {
      if (!this.draftVectorSource) return
      this.draftVectorSource.clear()
      const points = parsePoints(this.pointsText)
      for (const [lat, lng] of points) {
        this.draftVectorSource.addFeature(
          new Feature(new Point(fromLonLat([lng, lat])))
        )
      }
      if (points.length >= 2) {
        const coords = points.map(([lat, lng]) => fromLonLat([lng, lat]))
        coords.push(coords[0].slice())
        this.draftVectorSource.addFeature(new Feature(new Polygon([coords])))
      }
    },
    drawZones() {
      if (!this.zonesVectorSource) return
      this.zonesVectorSource.clear()
      for (const zone of this.zones) {
        if (zone.points && zone.points.length >= 2) {
          const coords = zone.points.map(([lat, lng]) => fromLonLat([lng, lat]))
          coords.push(coords[0].slice())
          const feature = new Feature(new Polygon([coords]))
          feature.set('zoneId', zone.id)
          feature.set('zoneDate', zone.date || '—')
          feature.set('zoneNotes', zone.notes || '')
          feature.set('markedForDeletion', !!zone.marked_for_deletion)
          this.zonesVectorSource.addFeature(feature)
        }
      }
    },
    async fetchUser() {
      try {
        const r = await fetch(API_AUTH_USER, { credentials: 'same-origin' })
        const data = await r.json()
        this.user = data
      } catch (_) {
        this.user = { is_authenticated: false }
      }
    },
    async fetchZones() {
      try {
        const r = await fetch(API_ZONES)
        if (r.ok) {
          const data = await r.json()
          this.zones = data
        }
      } catch (_) {
        this.zones = []
      }
      this.drawZones()
    },
    async saveZone() {
      const points = parsePoints(this.pointsText)
      if (points.length < 2 || !this.zoneDate) return
      try {
        const headers = { 'Content-Type': 'application/json' }
        const csrf = getCsrfToken()
        if (csrf) headers['X-CSRFToken'] = csrf
        const r = await fetch(API_ZONES, {
          method: 'POST',
          headers,
          body: JSON.stringify({ points, date: this.zoneDate || null, notes: (this.zoneNotes || '').trim() || null }),
          credentials: 'same-origin'
        })
        if (r.ok) {
          const zone = await r.json()
          this.zones.push(zone)
          this.pointsText = ''
          this.zoneNotes = ''
          this.zoneDate = new Date().toISOString().slice(0, 10)
          this.drawZones()
        } else {
          const err = await r.json().catch(() => ({}))
          alert(err.detail || err.points || 'Ошибка сохранения зоны')
        }
      } catch (e) {
        alert('Ошибка сети: ' + (e.message || 'не удалось сохранить зону'))
      }
    },
    openDeferredDelete(zone) {
      const d = new Date()
      d.setDate(d.getDate() + 7)
      this.deferredDeleteDate = d.toISOString().slice(0, 10)
      this.deferredDeleteZoneId = zone.id
    },
    async markForDeletion(zone) {
      if (!this.deferredDeleteDate) {
        alert('Укажите дату удаления')
        return
      }
      try {
        const headers = { 'Content-Type': 'application/json' }
        const csrf = getCsrfToken()
        if (csrf) headers['X-CSRFToken'] = csrf
        const r = await fetch(`${API_ZONES}${zone.id}/`, {
          method: 'DELETE',
          headers,
          body: JSON.stringify({ delete_after: this.deferredDeleteDate }),
          credentials: 'same-origin'
        })
        if (r.ok) {
          this.deferredDeleteZoneId = null
          await this.fetchZones()
        } else {
          const err = await r.json().catch(() => ({}))
          alert(err.detail || 'Не удалось пометить зону к удалению')
        }
      } catch (e) {
        alert('Ошибка сети: ' + (e.message || 'не удалось пометить зону к удалению'))
      }
    },
    async deleteImmediately(zone) {
      if (!confirm(`Удалить зону #${zone.id} (${zone.date || '—'}) сразу? Это действие нельзя отменить.`)) return
      try {
        const headers = {}
        const csrf = getCsrfToken()
        if (csrf) headers['X-CSRFToken'] = csrf
        const r = await fetch(`${API_ZONES}${zone.id}/delete-immediately/`, {
          method: 'POST',
          headers,
          credentials: 'same-origin'
        })
        if (r.ok) {
          this.zones = this.zones.filter(z => z.id !== zone.id)
          this.drawZones()
        } else {
          const err = await r.json().catch(() => ({}))
          alert(err.detail || 'Не удалось удалить зону')
        }
      } catch (e) {
        alert('Ошибка сети: ' + (e.message || 'не удалось удалить зону'))
      }
    },
    async cancelDeletion(zone) {
      try {
        const headers = {}
        const csrf = getCsrfToken()
        if (csrf) headers['X-CSRFToken'] = csrf
        const r = await fetch(`${API_ZONES}${zone.id}/cancel-deletion/`, {
          method: 'POST',
          headers,
          credentials: 'same-origin'
        })
        if (r.ok) {
          await this.fetchZones()
        } else {
          const err = await r.json().catch(() => ({}))
          alert(err.detail || 'Не удалось отменить удаление')
        }
      } catch (e) {
        alert('Ошибка сети: ' + (e.message || 'не удалось отменить удаление'))
      }
    },
    exportCsv() {
      if (this.zones.length === 0) return
      const rows = ['id;date;notes;points']
      for (const z of this.zones) {
        const pts = (z.points || []).map(p => `${p[0]},${p[1]}`).join(' ')
        const notes = (z.notes || '').replace(/"/g, '""')
        rows.push(`${z.id};${z.date || ''};"${notes}";"${pts}"`)
      }
      const csv = '\uFEFF' + rows.join('\n')
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `ptp_zones_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(a.href)
    }
  },
  watch: {
    zones() {
      this.drawZones()
    },
    pointsText() {
      this.drawDraft()
    },
    panelVisible() {
      this.$nextTick(() => this.map?.updateSize())
    }
  }
}
</script>

<style scoped>
.ptp-map {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a1a;
  color: #e0e0e0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #252525;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.auth {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auth .logout-form {
  display: inline;
}

.auth a.btn {
  text-decoration: none;
  display: inline-block;
}

.auth .input {
  width: 120px;
  padding: 6px 10px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #333;
  color: #fff;
  font-size: 14px;
}

.btn {
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: #42b983;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #35a372;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-outline {
  background: transparent;
  color: #42b983;
  border: 1px solid #42b983;
}

.btn-outline:hover {
  background: rgba(66, 185, 131, 0.15);
}

.btn-secondary {
  background: #555;
  color: #fff;
}

.btn-secondary:hover:not(:disabled) {
  background: #666;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
  margin-top: 8px;
}

.btn-small {
  padding: 2px 8px;
  font-size: 18px;
  line-height: 1.2;
  min-width: 28px;
}

.btn-danger {
  color: #f44336;
  border-color: #f44336;
}

.btn-danger:hover {
  background: rgba(244, 67, 54, 0.15);
}

.deferred-delete-inline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.deferred-delete-inline .input-date-small {
  width: 120px;
  padding: 2px 6px;
  font-size: 12px;
}

.zones-list {
  list-style: none;
  margin: 0 0 16px;
  padding: 0;
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.zone-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  margin-bottom: 4px;
  background: #333;
  border-radius: 4px;
  border: 1px solid #444;
  cursor: pointer;
}

.zone-item:hover {
  background: #3a3a3a;
  border-color: #555;
}

.zone-info {
  font-size: 13px;
  color: #ccc;
  flex: 1;
  min-width: 0;
}

.zone-info strong {
  color: #e0e0e0;
}

.zone-notes {
  display: block;
  font-size: 12px;
  color: #aaa;
  margin-top: 2px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 2.4em;
  overflow: hidden;
  text-overflow: ellipsis;
}

.zone-creator {
  display: block;
  font-size: 11px;
  color: #888;
  margin-top: 2px;
}

.zone-marked-deletion {
  display: block;
  font-size: 12px;
  color: #f44336;
  margin-top: 2px;
}

.zone-item--marked-for-deletion {
  border-color: #f44336;
  background: rgba(244, 67, 54, 0.08);
}

.zone-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.zones-empty {
  font-size: 13px;
  color: #888;
  margin: 0 0 16px;
}

.user {
  margin-right: 8px;
  font-size: 14px;
}

.auth-loading {
  font-size: 14px;
  color: #888;
}

.layout {
  display: flex;
  flex: 1;
  min-height: 0;
  position: relative;
}

.layout-panel-hidden .panel {
  width: 48px;
  min-width: 48px;
  padding: 8px;
}

.layout-panel-hidden .panel-header {
  justify-content: center;
  margin: 0;
}

.layout-panel-hidden .panel-content {
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  width: 0;
  height: 0;
  clip: rect(0, 0, 0, 0);
}

.panel {
  width: 320px;
  padding: 16px;
  background: #252525;
  border-right: 1px solid #333;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  transition: width 0.2s ease, padding 0.2s ease, min-width 0.2s ease;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -8px -8px 12px 0;
  flex-shrink: 0;
}

.coord-search {
  flex: 1;
  min-width: 0;
  padding: 6px 10px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #333;
  color: #fff;
  font-size: 13px;
}

.coord-search::placeholder {
  color: #666;
}

.panel-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  transition: opacity 0.2s ease;
}

.panel-toggle {
  flex-shrink: 0;
}

.textarea-notes {
  min-height: 48px;
}

.btn-icon {
  padding: 6px 10px;
  font-size: 18px;
  line-height: 1.2;
  min-width: 36px;
}

.map-container {
  position: relative;
  flex: 1;
  min-width: 0;
  background: #2d2d2d;
}

.map-container-inner {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.section h3 {
  font-size: 14px;
  margin: 0 0 12px;
  color: #ccc;
}

.section-zones {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.hint {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
  line-height: 1.4;
}

.textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #333;
  color: #fff;
  font-family: monospace;
  font-size: 13px;
  resize: vertical;
  margin-bottom: 10px;
}

.label {
  display: block;
  font-size: 12px;
  color: #aaa;
  margin-bottom: 4px;
}

.label .input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #333;
  color: #fff;
  font-size: 14px;
  margin-top: 4px;
}


.login-prompt {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 16px;
}
</style>
