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
const windowHalfX = window.innerWidth / 2
const windowHalfY = window.innerHeight / 2

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
  // Transparent background so CSS gradient shows through
  scene.background = null 

  // Camera
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 1000)
  camera.position.z = 500

  // Renderer
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(window.innerWidth, window.innerHeight)
  container.value.appendChild(renderer.domElement)

  // Particles
  particles = new THREE.Group()
  scene.add(particles)

  // Create individual particles
  const geometry = new THREE.BufferGeometry()
  const materials = new THREE.PointsMaterial({
    color: BASE_COLOR,
    size: PARTICLE_SIZE,
    transparent: true,
    opacity: 0.6
  })

  // We'll treat particles as simple points first, mimicking a network
  // To draw lines, we either need a custom shader or loop comfortably. 
  // Given < 200 particles, looping is fine for lines.
  
  // Let's create Sprite-based particles for better look
  const spriteMaterial = new THREE.SpriteMaterial({ 
    color: BASE_COLOR,
    transparent: true,
    opacity: 0.5
  })

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const particle = new THREE.Sprite(spriteMaterial)
    particle.position.x = Math.random() * 1000 - 500
    particle.position.y = Math.random() * 1000 - 500
    particle.position.z = Math.random() * 1000 - 500
    
    // Store velocity
    particle.userData = {
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      vz: (Math.random() - 0.5) * 0.5
    }
    
    particles.add(particle)
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
  particles.rotation.x += 0.0005
  particles.rotation.y += 0.001

  // Update particles
  const children = particles.children
  
  // Line geometry for connections
  // Note: Recreating geometry every frame is expensive, 
  // simplified approach: use LineSegments with BufferGeometry
  
  const linePositions: number[] = []
  const lineColors: number[] = [] // if we wanted color variation

  for (let i = 0; i < children.length; i++) {
    const particle = children[i] as THREE.Sprite
    const data = particle.userData

    // Move
    particle.position.x += data.vx
    particle.position.y += data.vy
    particle.position.z += data.vz

    // Bounce off walls (virtual box)
    if (particle.position.x < -500 || particle.position.x > 500) data.vx = -data.vx
    if (particle.position.y < -500 || particle.position.y > 500) data.vy = -data.vy
    if (particle.position.z < -500 || particle.position.z > 500) data.vz = -data.vz

    // Find connections
    // Limit connections to avoid N^2 performance hit if too high
    // Only check against a subset or just accept N^2 for N=150 (22500 checks is trivial for JS)
    for (let j = i + 1; j < children.length; j++) {
      const particleB = children[j]
      const dist = particle.position.distanceTo(particleB.position)

      if (dist < CONNECTION_DISTANCE) {
        // Opacity based on distance
        // Since we can't easily change alpha per segment in basic LineBasicMaterial without colors/attributes,
        // we'll just draw valid lines. For alpha fading, simplest is lines with constant low alpha.
        // Or specific BufferGeometry approach.
        
        linePositions.push(
          particle.position.x, particle.position.y, particle.position.z,
          particleB.position.x, particleB.position.y, particleB.position.z
        )
      }
    }
  }

  // Draw Lines
  // Remove old line mesh if exists
  const existingLines = scene.getObjectByName('lines')
  if (existingLines) scene.remove(existingLines)

  if (linePositions.length > 0) {
    const lineGeo = new THREE.BufferGeometry()
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3))
    
    const lineMat = new THREE.LineBasicMaterial({
      color: BASE_COLOR,
      transparent: true,
      opacity: 0.15
    })

    const lines = new THREE.LineSegments(lineGeo, lineMat)
    lines.name = 'lines'
    scene.add(lines)
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
