<script setup>
import { ref, shallowRef, onMounted, onUnmounted, nextTick, computed } from 'vue'
import gsap from 'gsap'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import ScrambleText from './components/ScrambleText.vue'

marked.setOptions({
  highlight: function (code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  langPrefix: 'hljs language-'
})

const renderMarkdown = (text) => {
  return DOMPurify.sanitize(marked.parse(text))
}


const chatHistory = ref([
  { role: 'assistant', text: 'I am AETHER. What realities shall we shape today?' }
])
const inputMessage = ref('')
const isGenerating = ref(false)
const chatContainerRef = ref(null)

const meshRef = shallowRef(null)
const light1Ref = shallowRef(null)
const light2Ref = shallowRef(null)

let animationFrameId = null
const startTime = Date.now()

// Scroll tracking for Parallax
const scrollY = ref(0)
const onScroll = (e) => {
  scrollY.value = e.target.scrollTop
}

// Mouse tracking
const mouse = { x: 0, y: 0 }
const delayedMouse1 = { x: 0, y: 0 }
const delayedMouse2 = { x: 0, y: 0 }
const delayedMouse3 = { x: 0, y: 0 }

const cursorRef = ref(null)
const ring1Ref = ref(null)
const ring2Ref = ref(null)
const ring3Ref = ref(null)

const windowHeight = ref(1080) // Default fallback

// --- Web Audio API for Cinematic UI Sounds ---
let audioCtx = null
let droneOsc1 = null
let droneOsc2 = null
let droneGain = null
let droneFilter = null

const initAudio = () => {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  if (audioCtx.state === 'suspended') audioCtx.resume()
  
  if (!droneOsc1) {
    droneOsc1 = audioCtx.createOscillator()
    droneOsc2 = audioCtx.createOscillator()
    droneGain = audioCtx.createGain()
    droneFilter = audioCtx.createBiquadFilter()
    
    droneOsc1.type = 'sine'
    droneOsc2.type = 'sine'
    droneOsc1.frequency.value = 55
    droneOsc2.frequency.value = 57
    
    droneFilter.type = 'lowpass'
    droneFilter.frequency.value = 200
    
    droneGain.gain.value = 0.03
    
    droneOsc1.connect(droneFilter)
    droneOsc2.connect(droneFilter)
    droneFilter.connect(droneGain)
    droneGain.connect(audioCtx.destination)
    
    droneOsc1.start()
    droneOsc2.start()
  }
}

const playFuturisticSound = (type) => {
  if (!audioCtx) return
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  osc.connect(gain)
  gain.connect(audioCtx.destination)

  const now = audioCtx.currentTime
  if (type === 'send') {
    // Clear audible sci-fi "send" blip
    osc.type = 'square'
    osc.frequency.setValueAtTime(400, now)
    osc.frequency.exponentialRampToValueAtTime(150, now + 0.2)
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(0.05, now + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2)
    osc.start(now)
    osc.stop(now + 0.2)
  } else if (type === 'done') {
    // Elegant bright chime when finished
    osc.type = 'sine'
    osc.frequency.setValueAtTime(1000, now)
    osc.frequency.exponentialRampToValueAtTime(2000, now + 0.5)
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(0.08, now + 0.05)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5)
    osc.start(now)
    osc.stop(now + 0.5)
  }
}
// ------------------------------------------

const onMouseMove = (e) => {
  mouse.x = e.clientX
  mouse.y = e.clientY
}

// Smooth scroll interpolation
let currentScrollY = 0

const renderLoop = () => {
  const elapsed = (Date.now() - startTime) * 0.001
  
  // Custom Cursor Physics
  delayedMouse1.x += (mouse.x - delayedMouse1.x) * 0.15
  delayedMouse1.y += (mouse.y - delayedMouse1.y) * 0.15
  delayedMouse2.x += (mouse.x - delayedMouse2.x) * 0.1
  delayedMouse2.y += (mouse.y - delayedMouse2.y) * 0.1
  delayedMouse3.x += (mouse.x - delayedMouse3.x) * 0.05
  delayedMouse3.y += (mouse.y - delayedMouse3.y) * 0.05

  if (cursorRef.value) gsap.set(cursorRef.value, { x: mouse.x, y: mouse.y })
  if (ring1Ref.value) gsap.set(ring1Ref.value, { x: delayedMouse1.x, y: delayedMouse1.y })
  if (ring2Ref.value) gsap.set(ring2Ref.value, { x: delayedMouse2.x, y: delayedMouse2.y })
  if (ring3Ref.value) gsap.set(ring3Ref.value, { x: delayedMouse3.x, y: delayedMouse3.y })

  // Smooth scroll lerping for 3D
  currentScrollY += (scrollY.value - currentScrollY) * 0.05

  if (droneFilter && droneOsc1 && droneOsc2 && audioCtx) {
    const scrollFactor = Math.min(currentScrollY / windowHeight.value, 3.0)
    droneFilter.frequency.setTargetAtTime(200 + scrollFactor * 400, audioCtx.currentTime, 0.1)
    droneOsc1.frequency.setTargetAtTime(55 - scrollFactor * 8, audioCtx.currentTime, 0.1)
    droneOsc2.frequency.setTargetAtTime(57 - scrollFactor * 8, audioCtx.currentTime, 0.1)
  }


  // 3D Glass Physics
  const targetX = (mouse.x / window.innerWidth) * 2 - 1
  const targetY = -(mouse.y / window.innerHeight) * 2 + 1
  
  if (meshRef.value) {
    // Medium rotation speed
    const speed = isGenerating.value ? 1.5 : 0.08
    
    // Scroll deeply affects X/Y rotation
    const scrollPhase = (currentScrollY / windowHeight.value)
    
    meshRef.value.rotation.y += speed * 0.016 + (targetX * 0.015)
    meshRef.value.rotation.x += (speed * 0.5) * 0.016 - (targetY * 0.015)
    
    // Add extra spin when scrolling
    meshRef.value.rotation.z = scrollPhase * 0.5
    
    // Trajectory for harmonious page following (Flawless Avoidance Route):
    // Phase 0 (Top): Right (x=2.5, y=0) - Chat is on Left
    // Phase 1 (Middle 1): Down/Right (x=2.5, y=-0.8) - Text is on Left
    // Phase 2 (Middle 2): Lower-Left (x=-2.0, y=-1.2) - Text is on Right
    // Phase 3+ (Bottom): Bottom-Left (x=-2.2, y=-1.3) - Footer is Center, FULLY VISIBLE
    let targetPosX = 2.5
    let targetPosY = 0
    
    if (scrollPhase < 1) {
      // "先向下走" (First go down, stay right)
      targetPosX = 2.5
      targetPosY = -(scrollPhase * 0.8)
    } else if (scrollPhase < 2) {
      // "再向左下走" (Then go to the lower left)
      const p = scrollPhase - 1
      targetPosX = 2.5 - (p * 4.5)
      targetPosY = -0.8 - (p * 0.4)
    } else {
      // "正好停在底边的左边与文字完美错开，全部露出来"
      const p = Math.min(scrollPhase - 2, 1.0)
      targetPosX = -2.0 - (p * 0.2)
      targetPosY = -1.2 - (p * 0.1)
    }
    
    // Smoothly apply the new X and Y positions
    meshRef.value.position.x += (targetPosX - meshRef.value.position.x) * 0.05
    meshRef.value.position.y += (targetPosY - meshRef.value.position.y) * 0.05

    // Smooth breathing effect
    const breath = isGenerating.value 
      ? 1.0 + Math.sin(elapsed * 8.0) * 0.04
      : 1.0 + Math.sin(elapsed * 1.5) * 0.015
    meshRef.value.scale.set(breath, breath, breath)
  }

  // Colored lights orbiting (medium speed)
  if (light1Ref.value) {
    light1Ref.value.color.setHex(isGenerating.value ? 0xffbb00 : 0xff0088)
    const orbitSpeed = isGenerating.value ? 3.0 : 0.6
    light1Ref.value.position.x = Math.sin(elapsed * orbitSpeed) * 3 + 2
    light1Ref.value.position.z = Math.cos(elapsed * orbitSpeed) * 3
  }
  if (light2Ref.value) {
    light2Ref.value.color.setHex(isGenerating.value ? 0xff2200 : 0x00ddff)
    const orbitSpeed = isGenerating.value ? 2.5 : 0.4
    light2Ref.value.position.x = Math.cos(elapsed * orbitSpeed) * 3 + 2
    light2Ref.value.position.z = Math.sin(elapsed * orbitSpeed) * 3
  }
  
  animationFrameId = requestAnimationFrame(renderLoop)
}

const uiRefs = ref([])

onMounted(() => {
  windowHeight.value = window.innerHeight
  window.addEventListener('resize', () => { windowHeight.value = window.innerHeight })
  window.addEventListener('mousemove', onMouseMove)
  mouse.x = window.innerWidth / 2
  mouse.y = window.innerHeight / 2
  delayedMouse1.x = delayedMouse2.x = delayedMouse3.x = mouse.x
  delayedMouse1.y = delayedMouse2.y = delayedMouse3.y = mouse.y

  renderLoop()

  // Cinematic Intro Animation (Safely simplified, no black overlay block)
  gsap.from('.fade-in-el', { y: 40, opacity: 0, duration: 2, stagger: 0.2, ease: 'expo.out', delay: 0.5 })
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
})

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isGenerating.value) return
  
  initAudio()
  playFuturisticSound('send')

  const msg = inputMessage.value
  inputMessage.value = ''
  
  chatHistory.value.push({ role: 'user', text: msg })
  chatHistory.value.push({ role: 'assistant', text: '' })
  scrollToBottom()
  
  isGenerating.value = true

  try {
    const response = await fetch('/api/vision/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      
      for (const line of lines) {
        if (line.trim() === '') continue
        if (line.startsWith('event:chunk')) continue
        if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim()
          if (dataStr === '[DONE]') {
            isGenerating.value = false
            playFuturisticSound('done')
            continue
          }
          try {
            const data = JSON.parse(dataStr)
            if (data.choices && data.choices[0].delta) {
              const content = data.choices[0].delta.content
              if (typeof content === 'string') {
                chatHistory.value[chatHistory.value.length - 1].text += content
                scrollToBottom()
              }
            }
          } catch(e) {}
        }
      }
    }
  } catch (e) {
    chatHistory.value[chatHistory.value.length - 1].text = 'Connection lost to the void.'
  } finally {
    isGenerating.value = false
  }
}
</script>

<template>
  <div class="relative w-full h-screen overflow-hidden bg-[#f0eee9] text-[#1a1a1a] font-serif cursor-none selection:bg-[#c0b8ab] selection:text-white" @click="initAudio">
    
    <!-- Cinematic Film Grain & Vignette -->
    <div class="noise-overlay absolute inset-0 z-[60] opacity-[0.25] mix-blend-overlay pointer-events-none"></div>
    <div class="absolute inset-0 z-[50] pointer-events-none vignette"></div>

    <!-- Multi-Ring Cursor -->
    <div ref="cursorRef" class="fixed top-0 left-0 w-2 h-2 bg-[#222] rounded-full pointer-events-none z-[70] -translate-x-1/2 -translate-y-1/2 mix-blend-difference shadow-[0_0_10px_rgba(255,255,255,0.8)]"></div>
    <div ref="ring1Ref" class="fixed top-0 left-0 w-8 h-8 border border-[#555] rounded-full pointer-events-none z-[70] -translate-x-1/2 -translate-y-1/2 mix-blend-difference" :class="isGenerating ? 'scale-75' : ''" style="transition: transform 0.3s"></div>
    <div ref="ring2Ref" class="fixed top-0 left-0 w-16 h-16 border border-[#888] rounded-full pointer-events-none z-[70] -translate-x-1/2 -translate-y-1/2 mix-blend-difference" :class="isGenerating ? 'scale-[1.5] border-[#ffaa00] border-2' : ''" style="transition: transform 0.5s, border-color 0.5s"></div>
    <div ref="ring3Ref" class="fixed top-0 left-0 w-24 h-24 border border-[#aaa] rounded-full pointer-events-none z-[70] -translate-x-1/2 -translate-y-1/2 mix-blend-difference" :class="isGenerating ? 'scale-[2.0] border-[#ff0088] border-2 opacity-50' : ''" style="transition: transform 0.7s, border-color 0.7s"></div>

    <!-- 3D Glass Object (FIXED in background) -->
    <div class="fixed inset-0 w-full h-full z-0 pointer-events-none">
      <TresCanvas clear-color="#f0eee9" alpha>
        <TresPerspectiveCamera :position="[0, 0, 7]" :fov="45" />
        
        <TresDirectionalLight :position="[5, 5, 5]" :intensity="3" color="#ffffff" />
        <TresAmbientLight :intensity="2.0" />
        <TresHemisphereLight skyColor="#ffffff" groundColor="#a8a39d" :intensity="1.5" />
        
        <TresPointLight ref="light1Ref" color="#ff0088" :intensity="20" :distance="15" />
        <TresPointLight ref="light2Ref" color="#00ddff" :intensity="20" :distance="15" />

        <TresMesh ref="meshRef" :position="[2.5, 0, 0]">
          <!-- Ultimate Cinema-quality Geometry -->
          <TresTorusKnotGeometry :args="[1.6, 0.5, 512, 128]" />
          <TresMeshPhysicalMaterial 
            color="#ffffff"
            :transmission="1.0"
            :opacity="1.0"
            :metalness="0.05"
            :roughness="0.01"
            :ior="1.55"
            :thickness="3.5"
            :specularIntensity="3.0"
            :clearcoat="1.0"
            :clearcoatRoughness="0.05"
            :iridescence="1.0"
            :iridescenceIOR="1.4"
          />
        </TresMesh>
      </TresCanvas>
    </div>

    <!-- SCROLLABLE FOREGROUND -->
    <div class="absolute inset-0 z-10 overflow-y-auto scrollbar-hide scroll-smooth" @scroll="onScroll">
      
      <!-- Section 1: Hero AI Chat UI -->
      <div class="relative w-full h-screen md:w-[45%] flex flex-col justify-between p-8 md:p-16 pointer-events-none">
        <!-- Container -->
        <div class="w-full h-full flex flex-col justify-between">
          <header class="fade-in-el pointer-events-auto cursor-none">
            <h1 class="text-5xl md:text-6xl font-medium tracking-[0.1em] uppercase mb-1 flex items-center gap-4 text-shadow-glow">
              <div class="w-4 h-4 rounded-full shadow-[0_0_15px_rgba(0,0,0,0.2)] transition-colors duration-300 border border-black/10" :class="isGenerating ? 'bg-[#ffaa00] animate-ping' : 'bg-white'"></div>
              A E T H E R
            </h1>
            <p class="text-[10px] text-[#555] tracking-[0.3em] uppercase font-sans mt-3 font-medium">Cognitive Matrix \ Scroll Down to Discover</p>
          </header>

          <main ref="chatContainerRef" class="fade-in-el flex-1 overflow-y-auto my-12 pr-6 pointer-events-auto flex flex-col gap-10 scrollbar-hide mask-gradient cursor-none">
            <div 
              v-for="(msg, i) in chatHistory" 
              :key="i"
              class="max-w-[95%] transition-all duration-700"
              :class="msg.role === 'user' ? 'self-end' : 'self-start'"
            >
              <div 
                class="text-[10px] tracking-[0.4em] uppercase mb-3 font-sans font-medium"
                :class="msg.role === 'user' ? 'text-[#888] text-right' : 'text-[#d4af37]'"
              >
                {{ msg.role === 'user' ? 'You' : 'Aether Core' }}
              </div>
              <div 
                class="text-2xl md:text-3xl font-light leading-relaxed whitespace-pre-wrap message-text"
                :class="[
                  msg.role === 'user' ? 'text-[#666] text-right italic' : 'text-[#111] markdown-body',
                  isGenerating && i === chatHistory.length - 1 && msg.role === 'assistant' ? 'glitch-text' : ''
                ]"
              >
                <template v-if="msg.role === 'user'">
                  {{ msg.text }}
                </template>
                <template v-else>
                  <ScrambleText :text="msg.text" :is-generating="isGenerating && i === chatHistory.length - 1" />
                  <span v-if="isGenerating && i === chatHistory.length - 1" class="w-2 h-6 inline-block bg-[#ffaa00] ml-1 align-middle animate-pulse"></span>
                </template>
              </div>
            </div>
          </main>

          <footer class="fade-in-el pointer-events-auto mt-auto cursor-none">
            <div class="relative group">
              <textarea 
                v-model="inputMessage"
                @keydown.enter.prevent="sendMessage"
                @focus="initAudio"
                placeholder="Shape reality here..."
                class="w-full bg-white/50 border border-white/80 rounded-3xl p-6 pr-20 font-sans text-sm focus:outline-none focus:border-black/30 focus:bg-white/80 transition-all resize-none text-[#111] backdrop-blur-xl shadow-[0_20px_60px_rgba(0,0,0,0.05)] cursor-none hover:shadow-[0_20px_60px_rgba(0,0,0,0.08)] font-medium"
                rows="1"
                style="min-height: 72px"
              ></textarea>
              <button 
                @click="sendMessage"
                :disabled="isGenerating || !inputMessage.trim()"
                class="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 flex items-center justify-center rounded-2xl bg-[#111] text-white transition-all duration-300 disabled:opacity-20 cursor-none hover:scale-110 shadow-[0_5px_20px_rgba(0,0,0,0.2)]"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </div>
            
            <!-- Scroll Indicator -->
            <div class="mt-12 text-[9px] text-[#777] tracking-[0.5em] uppercase text-center font-sans flex flex-col items-center gap-2 animate-bounce opacity-70">
              <span>Scroll to Explore</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
            </div>
          </footer>
        </div>
      </div>

      <!-- Section 2: Beyond Reality -->
      <div class="w-full min-h-screen flex items-center p-8 md:p-24 relative pointer-events-none mt-32">
        <div class="max-w-2xl text-left transition-transform duration-1000" :style="{ transform: `translateY(${(scrollY - windowHeight) * 0.15}px)` }">
          <p class="text-xs font-sans tracking-[0.4em] text-[#ffaa00] uppercase mb-4 font-semibold">01 / The Core</p>
          <h2 class="text-6xl md:text-[5.5rem] leading-[1.1] font-serif text-[#111] mb-8 font-medium">Beyond<br>Reality.</h2>
          <p class="text-xl md:text-2xl font-sans text-[#555] font-light leading-relaxed max-w-lg">
            Aether represents the bleeding edge of synthetic intelligence. Powered by the DeepSeek V4 matrix, it processes the fabric of human thought into immediate crystalline output.
          </p>
        </div>
      </div>

      <!-- Section 3: Aesthetics -->
      <div class="w-full min-h-screen flex items-center justify-end p-8 md:p-24 relative pointer-events-none mt-32 text-right">
        <div class="max-w-2xl transition-transform duration-1000" :style="{ transform: `translateY(${(scrollY - windowHeight*2) * 0.15}px)` }">
          <p class="text-xs font-sans tracking-[0.4em] text-[#ff0088] uppercase mb-4 font-semibold">02 / The Form</p>
          <h2 class="text-6xl md:text-[5.5rem] leading-[1.1] font-serif text-[#111] mb-8 font-medium">Absolute<br>Minimalism.</h2>
          <p class="text-xl md:text-2xl font-sans text-[#555] font-light leading-relaxed max-w-lg ml-auto">
            We stripped away the unnecessary. No bulky interfaces. No friction. Just you, the void, and an infinitely refracting physical mesh geometry.
          </p>
        </div>
      </div>
      
      <!-- Section 4: Footer -->
      <div class="w-full py-32 flex flex-col items-center justify-center pointer-events-auto cursor-none">
        <h3 class="text-3xl font-serif text-[#111] mb-4">A E T H E R</h3>
        <p class="text-xs font-sans tracking-[0.2em] text-[#777] uppercase">Engineered by ppday © 2026</p>
      </div>

    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Inter:wght@400;500;600&display=swap');

.font-serif { font-family: 'Playfair Display', serif; }
.font-sans { font-family: 'Inter', sans-serif; }

.noise-overlay {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
}

.vignette {
  box-shadow: inset 0 0 200px rgba(0,0,0,0.15);
}

.mask-gradient {
  mask-image: linear-gradient(to top, rgba(0,0,0,1) 5%, rgba(0,0,0,0) 100%);
  -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 10%, rgba(0,0,0,1) 95%, rgba(0,0,0,0) 100%);
}

.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }

.text-shadow-glow {
  text-shadow: 0 10px 30px rgba(0,0,0,0.05);
}

/* Subtle Chromatic Glitch Effect when typing */
.glitch-text {
  animation: rgb-shift 0.1s infinite alternate;
}
@keyframes rgb-shift {
  0% { text-shadow: 1px 0 0 rgba(255,0,0,0.2), -1px 0 0 rgba(0,0,255,0.2); }
  100% { text-shadow: -1px 0 0 rgba(255,0,0,0.2), 1px 0 0 rgba(0,0,255,0.2); }
}

.markdown-body p { margin-bottom: 1rem; }
.markdown-body pre {
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
  overflow-x: auto;
  font-size: 0.9rem;
  font-family: 'Courier New', Courier, monospace;
  color: #e0e0e0;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  margin-top: 1rem;
  margin-bottom: 1rem;
}
.markdown-body code:not(pre code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
  color: #ff0088;
}
.markdown-body ul { list-style-type: disc; margin-left: 1.5rem; margin-bottom: 1rem; }
.markdown-body ol { list-style-type: decimal; margin-left: 1.5rem; margin-bottom: 1rem; }
.markdown-body strong { font-weight: 600; color: #000; }
</style>

