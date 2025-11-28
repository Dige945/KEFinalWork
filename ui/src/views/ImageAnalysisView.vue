<template>
  <div class="image-analysis-view">
    <div class="page-header">
      <h2>
        <el-icon><Camera /></el-icon>
        图像分析与预测
      </h2>
      <p>基于AI的松材线虫病图像识别和智能诊断系统</p>
    </div>

    <div class="content-container">
      <ImageAnalysis />
    </div>

    <!-- 快速导航 -->
    <div class="quick-navigation">
      <el-card class="nav-card">
        <template #header>
          <div class="nav-header">
            <el-icon><Guide /></el-icon>
            快速导航
          </div>
        </template>
        
        <div class="nav-buttons">
          <router-link to="/" class="nav-link">
            <el-button type="primary" plain>
              <el-icon><Histogram /></el-icon>
              知识图谱
            </el-button>
          </router-link>
          
          <router-link to="/about" class="nav-link">
            <el-button type="info" plain>
              <el-icon><InfoFilled /></el-icon>
              关于系统
            </el-button>
          </router-link>
          
          <el-button type="success" plain @click="showHistory">
            <el-icon><Clock /></el-icon>
            分析历史
          </el-button>
          
          <el-button type="warning" plain @click="showHelp">
            <el-icon><QuestionFilled /></el-icon>
            使用帮助
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 分析历史对话框 -->
    <el-dialog
      v-model="historyDialogVisible"
      title="分析历史"
      width="800px"
    >
      <div v-if="historyLoading" class="loading-container">
        <el-icon class="is-loading" :size="40">
          <Loading />
        </el-icon>
        <p>加载中...</p>
      </div>
      
      <div v-else class="history-content">
        <div v-if="analysisHistory.length" class="history-list">
          <div
            v-for="(record, index) in analysisHistory"
            :key="record.id"
            class="history-item"
          >
            <div class="history-header">
              <span class="history-id">#{{ record.id }}</span>
              <span class="history-time">{{ record.timestamp }}</span>
              <el-tag :type="getRiskTagType(record.risk_level)">
                {{ record.risk_level }}
              </el-tag>
            </div>
            <div class="history-details">
              <div class="detail-item">
                <span class="label">检测实体:</span>
                <span class="value">{{ record.entity_count }} 个</span>
              </div>
              <div class="detail-item">
                <span class="label">实体类型:</span>
                <div class="entity-types">
                  <el-tag
                    v-for="type in record.detected_types"
                    :key="type"
                    size="small"
                    :type="getEntityTypeTag(type)"
                  >
                    {{ getEntityTypeLabel(type) }}
                  </el-tag>
                </div>
              </div>
              <div class="detail-item">
                <span class="label">整体置信度:</span>
                <el-progress
                  :percentage="record.confidence * 100"
                  :color="getConfidenceColor(record.confidence)"
                  :show-text="false"
                />
                <span class="confidence-text">{{ (record.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无分析历史" />
      </div>
    </el-dialog>

    <!-- 帮助对话框 -->
    <el-dialog
      v-model="helpDialogVisible"
      title="使用帮助"
      width="700px"
    >
      <div class="help-content">
        <el-collapse v-model="activeHelpItems" accordion>
          <el-collapse-item title="如何使用图像分析功能？" name="usage">
            <div class="help-section">
              <h4>操作步骤：</h4>
              <ol>
                <li>点击上传区域或拖拽图片到上传框</li>
                <li>选择合适的分析类型（推荐使用"完整分析"）</li>
                <li>调整置信度阈值（默认0.5，可根据需要调整）</li>
                <li>选择是否自动更新知识图谱</li>
                <li>等待系统完成分析</li>
                <li>查看分析结果的各个标签页</li>
              </ol>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="支持哪些类型的图片？" name="types">
            <div class="help-section">
              <h4>支持的图像类型：</h4>
              <ul>
                <li><strong>松树相关：</strong>马尾松、黑松等不同树种的叶片、树干、整株照片</li>
                <li><strong>昆虫相关：</strong>松墨天牛等传播媒介的特写或生态照片</li>
                <li><strong>病害症状：</strong>松针发黄、变红、脱落，树干流脂等症状照片</li>
                <li><strong>综合场景：</strong>包含多种元素的复合场景图像</li>
              </ul>
              
              <h4>文件格式要求：</h4>
              <ul>
                <li>支持格式：JPG、PNG、GIF</li>
                <li>文件大小：不超过10MB</li>
                <li>建议分辨率：800×600以上，以获得更好的识别效果</li>
              </ul>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="如何理解分析结果？" name="results">
            <div class="help-section">
              <h4>分析结果说明：</h4>
              <ul>
                <li><strong>实体识别：</strong>显示识别出的具体实体，包括类型、置信度和特征</li>
                <li><strong>关系分析：</strong>展示实体间的已知关系和AI推理的潜在关系</li>
                <li><strong>疾病预测：</strong>基于识别结果进行的疾病风险评估和预测</li>
                <li><strong>知识更新：</strong>系统自动添加到知识图谱的新信息统计</li>
              </ul>
              
              <h4>置信度解读：</h4>
              <ul>
                <li><strong>高置信度（80%以上）：</strong>识别结果可信度很高</li>
                <li><strong>中等置信度（60-80%）：</strong>识别结果基本可信，建议人工验证</li>
                <li><strong>低置信度（60%以下）：</strong>识别结果不确定，需要专家确认</li>
              </ul>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="系统有什么技术特点？" name="features">
            <div class="help-section">
              <h4>核心技术特点：</h4>
              <ul>
                <li><strong>多实体识别：</strong>能同时识别图像中的植物、昆虫、病症等多种实体</li>
                <li><strong>关系推理：</strong>基于知识图谱自动分析实体间的潜在关系</li>
                <li><strong>智能预测：</strong>结合专家知识和AI推理进行疾病风险预测</li>
                <li><strong>知识更新：</strong>自动将新发现的实体和关系更新到知识库</li>
                <li><strong>特征匹配：</strong>将识别特征与知识库中的标准特征进行比对</li>
              </ul>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Camera, Guide, Histogram, InfoFilled, Clock, QuestionFilled, Loading
} from '@element-plus/icons-vue'
import ImageAnalysis from '@/components/ImageAnalysis.vue'
import api from '@/api'

// 响应式数据
const historyDialogVisible = ref(false)
const helpDialogVisible = ref(false)
const historyLoading = ref(false)
const analysisHistory = ref([])
const activeHelpItems = ref(['usage'])

// 显示分析历史
const showHistory = async () => {
  historyDialogVisible.value = true
  historyLoading.value = true
  
  try {
    const result = await api.getAnalysisHistory(10)
    analysisHistory.value = result.history || []
  } catch (error) {
    ElMessage.error(`加载历史失败: ${error.message}`)
    analysisHistory.value = []
  } finally {
    historyLoading.value = false
  }
}

// 显示帮助
const showHelp = () => {
  helpDialogVisible.value = true
}

// 工具函数
const getRiskTagType = (risk) => {
  const types = {
    '高风险': 'danger',
    '中风险': 'warning',
    '低风险': 'success'
  }
  return types[risk] || 'info'
}

const getEntityTypeTag = (type) => {
  const tags = {
    'insect': 'danger',
    'tree': 'success',
    'disease_symptom': 'warning',
    'environment': 'info'
  }
  return tags[type] || ''
}

const getEntityTypeLabel = (type) => {
  const labels = {
    'insect': '昆虫',
    'tree': '植物',
    'disease_symptom': '病症',
    'environment': '环境'
  }
  return labels[type] || type
}

const getConfidenceColor = (confidence) => {
  if (confidence > 0.8) return '#67c23a'
  if (confidence > 0.6) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.image-analysis-view {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 30px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.page-header h2 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 10px;
  color: #303133;
  font-size: 32px;
}

.page-header p {
  color: #606266;
  font-size: 16px;
  margin: 0;
}

.content-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
  padding: 20px;
}

.quick-navigation {
  max-width: 800px;
  margin: 0 auto;
}

.nav-card {
  border-radius: 12px;
  overflow: hidden;
}

.nav-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}

.nav-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 10px 0;
}

.nav-link {
  text-decoration: none;
}

.nav-buttons .el-button {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.loading-container p {
  margin-top: 16px;
  font-size: 16px;
}

.history-content {
  max-height: 500px;
  overflow-y: auto;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
  transition: all 0.3s;
}

.history-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.history-id {
  font-weight: 600;
  color: #409eff;
}

.history-time {
  color: #909399;
  font-size: 14px;
}

.history-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-item .label {
  color: #606266;
  font-size: 14px;
  min-width: 80px;
}

.detail-item .value {
  color: #303133;
  font-weight: 500;
}

.entity-types {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.confidence-text {
  margin-left: 8px;
  color: #606266;
  font-size: 12px;
}

.help-content {
  max-height: 600px;
  overflow-y: auto;
}

.help-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.help-section ul,
.help-section ol {
  margin: 8px 0;
  padding-left: 20px;
}

.help-section li {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
}

.help-section strong {
  color: #303133;
  font-weight: 600;
}

@media (max-width: 768px) {
  .image-analysis-view {
    padding: 10px;
  }
  
  .page-header {
    padding: 20px 10px;
  }
  
  .page-header h2 {
    font-size: 24px;
  }
  
  .nav-buttons {
    grid-template-columns: 1fr;
  }
  
  .content-container {
    padding: 10px;
  }
}
</style>