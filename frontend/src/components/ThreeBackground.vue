<template>
  <div ref="container" class="three-background"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'

const container = ref<HTMLElement | null>(null)
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let particles: THREE.Group
let animationFrameId: number

// Configuration
const PARTICLE_COUNT = 150
const CONNECTION_DISTANCE = 150
const PARTICLE_SIZE = 2
const BASE_COLOR = 0x000000 // Black lines/nodes for light mode

// Mouse interaction
let mouseX = 0
let mouseY = 0
let targetX = 0
let targetY = 0
let windowHalfX = window.innerWidth / 2
let windowHalfY = window.innerHeight / 2

onMounted(() => {
  init()
  animate()
  window.addEventListener('resize', onWindowResize)
  document.addEventListener('mousemove', onDocumentMouseMove)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  document.removeEventListener('mousemove', onDocumentMouseMove)
  cancelAnimationFrame(animationFrameId)
  
  if (renderer) {
    renderer.dispose()
  }
})

function init() {
  if (!container.value) return

  // Scene
  scene = new THREE.Scene()
  // Background set to grey
  scene.background = new THREE.Color(0x808080)

  // Camera
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 1000)
  camera.position.z = 500

  // Renderer
  renderer = new THREE.WebGLRenderer({ alpha: false, antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(window.innerWidth, window.innerHeight)
  container.value.appendChild(renderer.domElement)

  // Books group
  particles = new THREE.Group()
  scene.add(particles)

  // Simple box geometry to represent a book (cover + spine)
  const bookGeometry = new THREE.BoxGeometry(20, 12, 3)
  const coverMat = new THREE.MeshPhongMaterial({ color: 0x111111 })
  const spineMat = new THREE.MeshPhongMaterial({ color: 0x333333 })

  // light for subtle shading
  const light = new THREE.DirectionalLight(0xffffff, 0.6)
  light.position.set(1, 1, 1)
  scene.add(light)
  const amb = new THREE.AmbientLight(0xffffff, 0.4)
  scene.add(amb)

  for (let i = 0; i < Math.min(PARTICLE_COUNT, 40); i++) {
    const book = new THREE.Mesh(bookGeometry, coverMat)
    book.position.x = Math.random() * 1000 - 500
    book.position.y = Math.random() * 700 - 350
    book.position.z = Math.random() * 800 - 400

    // Rotate slightly to look natural
    book.rotation.x = (Math.random() - 0.5) * 0.5
    book.rotation.y = (Math.random() - 0.5) * 0.5
    book.rotation.z = (Math.random() - 0.5) * 0.5

    book.userData = {
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      vz: (Math.random() - 0.5) * 0.6
    }

    particles.add(book)
  }
}

function onWindowResize() {
  const width = window.innerWidth
  const height = window.innerHeight
  
  windowHalfX = width / 2
  windowHalfY = height / 2

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

function onDocumentMouseMove(event: MouseEvent) {
  mouseX = (event.clientX - windowHalfX) * 0.05
  mouseY = (event.clientY - windowHalfY) * 0.05
}

function animate() {
  animationFrameId = requestAnimationFrame(animate)
  render()
}

function render() {
  // Smooth camera follow
  targetX = mouseX * 0.1
  targetY = mouseY * 0.1
  
  // Rotate entire group slowly
  particles.rotation.x += 0.0008
  particles.rotation.y += 0.0012

  // Update books
  const children = particles.children
  for (let i = 0; i < children.length; i++) {
    const book = children[i]
    const data = book.userData

    // Move
    book.position.x += data.vx
    book.position.y += data.vy
    book.position.z += data.vz

    // subtle rotation
    book.rotation.x += 0.002 * (i % 3)
    book.rotation.y += 0.003 * (i % 2)

    // Bounce off bounds
    if (book.position.x < -600 || book.position.x > 600) data.vx = -data.vx
    if (book.position.y < -400 || book.position.y > 400) data.vy = -data.vy
    if (book.position.z < -600 || book.position.z > 600) data.vz = -data.vz
  }

  // Camera sway
  camera.position.x += (mouseX - camera.position.x) * 0.05
  camera.position.y += (-mouseY - camera.position.y) * 0.05
  camera.lookAt(scene.position)

  renderer.render(scene, camera)
}
</script>

<style scoped>
.three-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
  pointer-events: none; /* Let clicks pass through */
}
</style>
