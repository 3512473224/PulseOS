<template>
  <div v-html="renderedHtml" class="w-full"></div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

marked.setOptions({
  highlight: function (code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  langPrefix: 'hljs language-'
})

const props = defineProps({
  text: {
    type: String,
    required: true
  },
  isGenerating: {
    type: Boolean,
    default: false
  }
})

const displayText = ref('')
const chars = '!<>-_\\\\/[]{}—=+*^?#________'
let scrambleInterval = null

const scramble = (newText, oldText) => {
  if (props.isGenerating && newText.length > oldText.length && newText.startsWith(oldText)) {
    const newPart = newText.slice(oldText.length)
    let iterations = 0
    const maxIterations = 3
    
    clearInterval(scrambleInterval)
    scrambleInterval = setInterval(() => {
      if (iterations >= maxIterations) {
        clearInterval(scrambleInterval)
        displayText.value = newText
      } else {
        const scrambledPart = newPart.split('').map(char => {
          if (char === ' ' || char === '\n') return char
          return chars[Math.floor(Math.random() * chars.length)]
        }).join('')
        displayText.value = oldText + scrambledPart
      }
      iterations++
    }, 30)
  } else {
    displayText.value = newText
  }
}

watch(() => props.text, (newVal, oldVal) => {
  scramble(newVal, oldVal || '')
})

onMounted(() => {
  displayText.value = props.text
})

const renderedHtml = computed(() => {
  return DOMPurify.sanitize(marked.parse(displayText.value))
})
</script>
