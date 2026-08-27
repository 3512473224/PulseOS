<template>
  <span v-html="displayText" class="scramble-text"></span>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

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
  // Only scramble the newly added part if it's generating
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
          // preserve spaces and basic html tags to not break rendering
          if (char === ' ' || char === '\n' || char === '<' || char === '>') return char
          return chars[Math.floor(Math.random() * chars.length)]
        }).join('')
        displayText.value = oldText + scrambledPart
      }
      iterations++
    }, 30) // 30ms per scramble frame
  } else {
    // If not appending or not generating, just set it directly
    displayText.value = newText
  }
}

watch(() => props.text, (newVal, oldVal) => {
  scramble(newVal, oldVal || '')
})

onMounted(() => {
  displayText.value = props.text
})
</script>

<style scoped>
.scramble-text {
  transition: all 0.1s ease;
}
</style>
