<!--
 * @Author: 熊泽仁
 * 2025-07-03
 * 更新记录:
      webrtc播放器设置
-->

<template>
    <video
      ref="videoElement"
      controls
      autoplay
      muted
      class="rounded"
      style="width: 100%; height: auto; background-color: black"
    />
  </template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { JSWebrtc } from '/@/vendors/jswebrtc.js'
const videoElement = ref<HTMLVideoElement | null>(null)
let player: JSWebrtc.Player | null = null

const props = defineProps({
  src: {
    type: String,
    required: true,
  },
})

const initPlayer = () => {
  if (!videoElement.value) return

  if (player) {
    player.destroy()
    player = null
  }

  player = new JSWebrtc.Player(props.src, {
    video: videoElement.value,
    autoplay: true,
    onPlay: (obj: any) => {
      console.log('start play', obj)
    },
    onError: (error: Error) => {
      console.error('Playback error:', error)
    }
  })
}

watch(() => props.src, () => {
  initPlayer()
})

onMounted(() => {
  initPlayer()
})

onBeforeUnmount(() => {
  player?.destroy()
  player = null
})
</script>

<style scoped>
  video {
    border-radius: 6px;
  }
</style>
