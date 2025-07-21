<!--
 * @Author: 熊泽仁
 * 2025-07-03
 * 更新记录:
    组件集成，状态信息表内容更新
-->
<template>
  <div class="p-6 space-y-6 bg-gray-50 min-h-screen">
    <!-- 控制设置组件 -->
    <StreamSettings @status-update="fetchStatus" />

    <!-- 视频播放区域 -->

    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <webrtcplayer
        v-for="(s, idx) in Object.values(statusMap)"
        :key="idx"
        :src="`${CURRENT_CONFIG.webrtc}${s.stream_id}`"
        class="rounded shadow border border-gray-300"
      />
    </div>

    <!-- 状态信息表 -->
    <a-table
      class="mt-4"
      :dataSource="Object.values(statusMap)"
      :columns="columns"
      rowKey="stream_id"
      bordered
      size="small"
      :pagination="false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import webrtcplayer from '/@/components/webrtcplayer.vue'
import StreamSettings from '/@/components/StreamSettings.vue'

import { CURRENT_CONFIG } from '/@/api/http/config'

// 状态记录
const statusMap = reactive({})

// 状态表格列定义
const columns = [
  { title: '流 ID', dataIndex: 'stream_id' },
  { title: '推流状态', dataIndex: 'push_status' },
  { title: 'AI推理状态', dataIndex: 'ai_status' },
  { title: '录制状态', dataIndex: 'record_status' },
  { title: 'FPS', dataIndex: 'fps' },
  { title: '帧数', dataIndex: 'frame_count' },
  { title: '更新时间', dataIndex: 'last_update' },
]

// 用于组件通信时主动拉取状态（可选）
const fetchStatus = async () => {
  try {
    const res = await axios.get(`${CURRENT_CONFIG.fastapiBase || 'http://192.168.101.6:8000'}/status`)
    Object.assign(statusMap, res.data)
  } catch (err) {
    console.error('状态获取失败', err)
  }
}

// 页面加载时自动建立 websocket 状态连接
onMounted(() => {
  const ws = new WebSocket(`${CURRENT_CONFIG.aiWebSocketURL || 'ws://192.168.101.6:8000'}/ws/status`)
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    Object.assign(statusMap, data)
  }
})
</script>

<style scoped>
video {
  border-radius: 6px;
  background-color: black;
  width: 100%;
  height: auto;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}
</style>
