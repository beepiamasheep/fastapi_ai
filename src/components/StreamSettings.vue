<!--
 * @Author: 熊泽仁
 * 2025-07-03
 * 更新记录:
    完成推流信息输入
    视频流推流控制
    视频流录制任意长控制
-->
<template>

  <div class="form-container">
    <a-form layout="inline" @submit.prevent style="display: flex; align-items: center;">
      <!-- IP地址 -->
      <a-form-item label="IP地址">
        <a-input
          v-model:value="ipAddress"
          placeholder="192.168.1.1"
          style="width: 160px;"
        />
      </a-form-item>

       <!-- 应用名 -->
      <a-form-item label="应用名">
        <a-input
          v-model:value="appName"
          placeholder="live"
          style="width: 160px;"
        />
      </a-form-item>

      <!-- 流名称 -->
      <a-form-item label="流名称">
        <a-input
          v-model:value="streamName"
          placeholder="test"
          style="width: 160px;"
        />
      </a-form-item>

      <!-- 分辨率 -->
      <a-form-item label="分辨率">
        <div style="display: flex; align-items: center; gap: 4px;">
          <a-input-number
            v-model:value="width"
            placeholder="1980"
            :min="320"
            style="width: 80px;"
          />
          <span>×</span>
          <a-input-number
            v-model:value="height"
            placeholder="720"
            :min="240"
            style="width: 80px;"
          />
        </div>
      </a-form-item>

      <!-- 帧率 -->
      <a-form-item label="帧率">
        <a-input-number
          v-model:value="fps"
          placeholder="30"
          :min="5"
          :max="60"
          style="width: 100px;"
        />
      </a-form-item>

      <!-- AI 推理 -->
      <a-form-item>
        <a-checkbox v-model:checked="aiEnabled">AI 推理</a-checkbox>
      </a-form-item>

      <!-- 操作按钮区 -->
      <a-form-item style="margin-left: auto;">
        <div style="display: flex; gap: 8px;">
          <a-button type="primary" @click="push_start">推流启动</a-button>
          <a-button danger @click="push_stop">推流停止</a-button>
          <a-button type="primary" @click="record_start">录制启动</a-button>
          <a-button danger @click="record_stop">录制停止</a-button>
        </div>
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { CURRENT_CONFIG } from '/@/api/http/config'

const emit = defineEmits(['status-update'])
const ipAddress = ref('192.168.101.10') // IP名称
const appName = ref('live') // 应用名称
const streamName = ref('stream33') // 流名称
const width = ref(1280) // 视频宽度
const height = ref(720) // 视频高度
const fps = ref(30) // 帧率
const aiEnabled = ref(true) // AI推理开关
const recordEnabled = ref(false) // 本地录制开关

// 推理启动
const push_start = async () => {
  const name = streamName.value.trim()
  const ipaddress = ipAddress.value.trim()
  const appname = appName.value.trim()

  if (!name || !ipaddress || !appname) {
    return
  }

  // 构建请求参数
  const params = {
    input_stream: `rtmp://${ipaddress.value}:1935/${appname}/${name}`, // 输入流地址
    width: width.value,
    height: height.value, // 分辨率
    fps: fps.value, // 帧率
    ai_enabled: aiEnabled.value, // AI开关
    record_enabled: recordEnabled.value // 录制开关
  }

  // 调用后端API启动流
  await axios.post(`${CURRENT_CONFIG.aiServiceURL || 'http://192.168.101.6:8000'}/start-stream`, params)
  emit('status-update') // 通知父组件状态变更
}

// 推流停止
const push_stop = async () => {
  let name = streamName.value.trim()
  const ipaddress = ipAddress.value.trim()
  const appname = appName.value.trim()
  const aienabled = aiEnabled.value

  if (!name || !ipaddress || !appname) {
    return
  }

  if (aienabled) {
    name = `${name}_mask`
  }

  // 调用后端API停止流，通过URL参数指定流ID
  await axios.post(`${CURRENT_CONFIG.aiServiceURL || 'http://192.168.101.6:8000'}/stop-stream`, null, {
    params: { stream_id: name }
  })
  emit('status-update') // 通知父组件状态变更
}

// 录制启动
const record_start = async () => {
  let name = streamName.value.trim()
  const ipaddress = ipAddress.value.trim()
  const appname = appName.value.trim()
  const aienabled = aiEnabled.value

  if (!name || !ipaddress || !appname) {
    return
  }

  if (aienabled) {
    name = `${name}_mask`
  }

  // 构建请求参数
  const record_params = {
    stream_id: name, // 录制视频流id
    input_stream: `rtmp://${ipaddress}:1935/${appname}/${name}` // 输入流地址
  }

  // 调用后端API启动流
  await axios.post(`${CURRENT_CONFIG.aiServiceURL || 'http://192.168.101.6:8000'}/start-record`, record_params)
  emit('status-update') // 通知父组件状态变更
}

// 录制停止
const record_stop = async () => {
  let name = streamName.value.trim()
  const ipaddress = ipAddress.value.trim()
  const appname = appName.value.trim()
  const aienabled = aiEnabled.value

  if (!name || !ipaddress || !appname) {
    return
  }

  if (aienabled) {
    name = `${name}_mask`
  }

  // 调用后端API停止流，通过URL参数指定流ID
  await axios.post(`${CURRENT_CONFIG.aiServiceURL || 'http://192.168.101.6:8000'}/stop-record`, null, {
    params: { record_stream_id: name }
  })
  emit('status-update') // 通知父组件状态变更
}
</script>

<style scoped>
/* 包裹表单的容器 */
.form-container {
  background-color: white;
  padding: 5px 20px 5px 20px;
  border-radius: 0px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 0;
}
</style>
