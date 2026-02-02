<template>
  <div class="ptp-map">
    <header class="header">
      <h1 class="title">Закрытая карта PTP</h1>
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
          <a href="/oidc/authenticate/" class="btn btn-primary">Войти (OIDC)</a>
        </template>
      </div>
    </header>

    <div v-if="user === null" class="login-prompt">
      <p>Проверка авторизации…</p>
    </div>
    <div v-else-if="!user.is_authenticated" class="login-prompt">
      <p>Войдите через OIDC (Keycloak), чтобы работать с картой и зонами.</p>
    </div>
    <div v-else class="layout">
      <aside class="panel">
        <section class="section">
          <h3>Добавить зону (ввод точек построчно)</h3>
          <p class="hint">Одна точка на строку: широта пробел долгота, например: 55.7558 37.6173</p>
          <textarea
            v-model="pointsText"
            class="textarea"
            rows="6"
            placeholder="55.7558 37.6173&#10;55.7512 37.6185&#10;55.7520 37.6200"
          />
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
      </aside>
      <div ref="mapContainer" class="map-container"></div>
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
import { fromLonLat } from 'ol/proj'
import Style from 'ol/style/Style'
import Fill from 'ol/style/Fill'
import Stroke from 'ol/style/Stroke'
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
      user: null,
      pointsText: '',
      zoneDate: new Date().toISOString().slice(0, 10),
      zones: []
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
    initMap() {
      if (!this.$refs.mapContainer) return
      this.zonesVectorSource = new VectorSource()
      const osmLayer = new TileLayer({ source: new OSM() })
      const zonesLayer = new VectorLayer({
        source: this.zonesVectorSource,
        style: new Style({
          fill: new Fill({ color: 'rgba(33, 150, 243, 0.2)' }),
          stroke: new Stroke({ color: '#2196F3', width: 2 })
        })
      })
      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [osmLayer, zonesLayer],
        view: new View({
          center: fromLonLat([37.6173, 55.7558]),
          zoom: 10
        })
      })
      this.drawZones()
    },
    drawZones() {
      if (!this.zonesVectorSource) return
      this.zonesVectorSource.clear()
      for (const zone of this.zones) {
        if (zone.points && zone.points.length >= 2) {
          const coords = zone.points.map(([lat, lng]) => fromLonLat([lng, lat]))
          coords.push(coords[0].slice())
          const feature = new Feature(new Polygon([coords]))
          feature.set('zoneDate', zone.date || '—')
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
          body: JSON.stringify({ points, date: this.zoneDate || null }),
          credentials: 'same-origin'
        })
        if (r.ok) {
          const zone = await r.json()
          this.zones.push(zone)
          this.pointsText = ''
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
    exportCsv() {
      if (this.zones.length === 0) return
      const rows = ['id;date;points']
      for (const z of this.zones) {
        const pts = (z.points || []).map(p => `${p[0]},${p[1]}`).join(' ')
        rows.push(`${z.id};${z.date || ''};"${pts}"`)
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
}

.panel {
  width: 320px;
  padding: 16px;
  background: #252525;
  border-right: 1px solid #333;
  overflow-y: auto;
  flex-shrink: 0;
}

.section h3 {
  font-size: 14px;
  margin: 0 0 12px;
  color: #ccc;
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

.map-container {
  flex: 1;
  min-width: 0;
  background: #2d2d2d;
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
