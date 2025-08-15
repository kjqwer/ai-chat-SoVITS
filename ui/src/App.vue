<script setup>
import { ref, onMounted, computed } from 'vue'
import { useApiStore } from './stores/api.js'
import SettingsPage from './components/SettingsPage.vue'
import ChatPage from './components/Page2.vue'
import ConfigPage from './components/ConfigPage.vue'
import ASRPage from './components/ASRPage.vue'
import { Setting, ChatDotRound, Tools, Microphone } from '@element-plus/icons-vue'

const apiStore = useApiStore()

// 当前激活的菜单项
const activeMenu = ref('settings')

// 系统状态
const systemStatus = computed(() => apiStore.systemStatus)
const isLoading = computed(() => apiStore.isLoading)

// 菜单选择处理
const handleMenuSelect = (index) => {
  activeMenu.value = index
}

// 组件挂载时初始化数据
onMounted(async () => {
  try {
    await apiStore.initializeData()
  } catch (error) {
    console.error('Failed to initialize app:', error)
  }
})
</script>

<template>
  <div id="app">
    <el-container style="height: 100vh;">
      <!-- 左侧菜单 -->
      <el-aside width="250px" style="background-color: #304156;">
        <div class="sidebar-header">
          <h2 style="color: white; text-align: center; margin: 20px 0;">GPT-SoVITS</h2>
        </div>

        <el-menu :default-active="activeMenu" class="sidebar-menu" background-color="#304156" text-color="#bfcbd9"
          active-text-color="#409EFF" @select="handleMenuSelect">
          <el-menu-item index="settings">
            <el-icon>
              <Setting />
            </el-icon>
            <span>设置</span>
          </el-menu-item>

          <el-menu-item index="page2">
            <el-icon>
              <ChatDotRound />
            </el-icon>
            <span>AI对话</span>
          </el-menu-item>

          <el-menu-item index="config">
            <el-icon>
              <Tools />
            </el-icon>
            <span>配置管理</span>
          </el-menu-item>

          <el-menu-item index="asr">
            <el-icon>
              <Microphone />
            </el-icon>
            <span>语音识别</span>
          </el-menu-item>
        </el-menu>

        <!-- 系统状态显示 -->
        <div class="system-status" v-if="systemStatus">
          <el-divider style="border-color: #445266;" />
          <div class="status-item">
            <span style="color: #bfcbd9; font-size: 12px;">当前模型:</span>
            <div style="color: #409EFF; font-size: 12px; word-break: break-all;">
              {{ systemStatus.current_sovits_model || '未设置' }}
            </div>
          </div>
          <div class="status-item">
            <span style="color: #bfcbd9; font-size: 12px;">当前角色:</span>
            <div style="color: #409EFF; font-size: 12px;">
              {{ systemStatus.current_character || '未设置' }}
            </div>
          </div>
          <div class="status-item">
            <span style="color: #bfcbd9; font-size: 12px;">设备:</span>
            <div style="color: #67C23A; font-size: 12px;">
              {{ systemStatus.device || 'N/A' }}
            </div>
          </div>
        </div>
      </el-aside>

      <!-- 右侧内容区 -->
      <el-main style="padding: 0;">
        <div class="main-content">
          <!-- 设置页面 -->
          <SettingsPage v-if="activeMenu === 'settings'" />

          <!-- AI对话页面 -->
          <ChatPage v-else-if="activeMenu === 'page2'" />

          <!-- 配置管理页面 -->
          <ConfigPage v-else-if="activeMenu === 'config'" />

          <!-- ASR语音识别页面 -->
          <ASRPage v-else-if="activeMenu === 'asr'" />

          <!-- 默认页面 -->
          <div v-else class="welcome-page">
            <el-empty description="请选择左侧菜单项" />
          </div>
        </div>
      </el-main>
    </el-container>

    <!-- 全局加载状态 -->
    <el-loading v-loading="isLoading" element-loading-text="加载中..." element-loading-background="rgba(0, 0, 0, 0.3)"
      :element-loading-lock="true" v-if="false" />
  </div>
</template>

<style scoped>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu .el-menu-item {
  border-radius: 6px;
  margin: 5px 15px;
  padding-left: 20px !important;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #263445 !important;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #409EFF !important;
  color: white !important;
}

.main-content {
  height: 100vh;
  overflow-y: auto;
  background-color: #f5f5f5;
}

.welcome-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.system-status {
  position: absolute;
  bottom: 20px;
  left: 15px;
  right: 15px;
}

.status-item {
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>

<style>
body {
  margin: 0;
  padding: 0;
}

.el-aside {
  position: relative;
}
</style>
