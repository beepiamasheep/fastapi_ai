<!--
 * @Author: 熊泽仁
 * 2025-07-03
 * 更新记录:
-->
<template>
    <video
      ref="videoRef"
      controls
      autoplay
      muted
      class="rounded"
      style="width: 100%; height: auto; background-color: black"
    />
  </template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import flvjs from 'flv.js'

const props = defineProps({
  src: {
    type: String,
    required: true,
  },
})

const videoRef = ref(null)
let player = null

const initPlayer = () => {
  if (player) {
    player.destroy()
    player = null
  }
  if (flvjs.isSupported() && props.src) {
    player = flvjs.createPlayer({
      type: 'flv',
      url: props.src,
    })
    player.attachMediaElement(videoRef.value)
    player.load()
    player.play().catch(() => {
      // 避免加载失败卡死
      console.warn(`[FlvPlayer] play() failed for: ${props.src}`)
    })
  }
}

// 自动重新加载推流地址变更时
watch(() => props.src, () => {
  initPlayer()
})

onMounted(() => {
  initPlayer()
})

onBeforeUnmount(() => {
  if (player) {
    player.destroy()
    player = null
  }
})
</script>

<style scoped>
  video {
    border-radius: 6px;
  }
</style>
