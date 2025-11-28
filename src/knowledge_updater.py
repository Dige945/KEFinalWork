"""
知识图谱动态更新服务
当识别结果相似度低于阈值时，自动将新实体、特征或关系插入知识图谱
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from contextlib import contextmanager
import pymysql

logger = logging.getLogger(__name__)


class KnowledgeGraphUpdater:
    """知识图谱动态更新器"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化知识图谱更新器
        
        Args:
            db_config: 数据库配置
        """
        self.db_config = db_config
        self.similarity_threshold = 0.6  # 相似度阈值
        self.confidence_threshold = 0.5  # 识别置信度阈值
        
        # 新实体类型映射
        self.entity_type_mapping = {
            "insect": "昆虫",
            "disease_symptom": "症状", 
            "tree": "植物",
            "plant": "植物",
            "environment": "环境因子",
            "vehicle": "交通工具",
            "building": "建筑设施",
            "natural": "自然环境",
            "industrial": "工业物品",
            "other": "其他"
        }
        
        logger.info("知识图谱更新器初始化完成")
    
    @contextmanager
    def get_db(self):
        """数据库连接上下文管理器"""
        conn = pymysql.connect(**self.db_config)
        try:
            yield conn
        finally:
            conn.close()
    
    async def process_image_analysis_result(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理图像分析结果，决定是否需要更新知识图谱
        
        Args:
            analysis_result: 图像分析结果
            
        Returns:
            更新结果统计
        """
        update_stats = {
            "new_entities_added": 0,
            "new_relations_added": 0,
            "features_updated": 0,
            "skipped_low_confidence": 0,
            "updates": []
        }
        
        detected_entities = analysis_result.get("detected_entities", [])
        
        try:
            with self.get_db() as conn:
                for entity in detected_entities:
                    # 检查是否需要添加新实体
                    if await self._should_add_entity(entity):
                        await self._add_new_entity(conn, entity, update_stats)
                    
                    # 检查是否需要添加新关系
                    if len(detected_entities) > 1:
                        await self._process_entity_relationships(conn, detected_entities, update_stats)
                
                # 处理实体间的关系发现
                await self._discover_and_add_relationships(conn, detected_entities, update_stats)
                
            logger.info(f"知识图谱更新完成: {update_stats}")
            return update_stats
            
        except Exception as e:
            logger.error(f"知识图谱更新失败: {e}")
            raise
    
    async def _should_add_entity(self, entity: Dict[str, Any]) -> bool:
        """
        判断是否应该添加新实体
        
        Args:
            entity: 检测到的实体
            
        Returns:
            是否应该添加
        """
        # 置信度太低，跳过
        if entity["confidence"] < self.confidence_threshold:
            return False
        
        # 相似度高，说明已存在类似实体
        if entity["similarity"] > self.similarity_threshold:
            return False
        
        # 特殊处理：如果是"未知实体"格式，检查实际实体是否已存在
        entity_name = entity["name"]
        if entity_name.startswith("未知实体:") or entity_name.startswith("未知实体："):
            # 提取实际实体名称
            actual_name = entity_name.split(":", 1)[1].strip() if ":" in entity_name else entity_name.split("：", 1)[1].strip()
            
            # 检查数据库中是否已存在该实体
            if self._entity_exists_in_db(actual_name):
                logger.info(f"实体 {actual_name} 已存在于数据库中，跳过未知实体 {entity_name} 的添加")
                return False
        
        # 没有匹配的知识库实体，且置信度足够高
        if not entity.get("matched_kb_entity") and entity["confidence"] > 0.7:
            return True
        
        return False
    
    def _entity_exists_in_db(self, entity_name: str) -> bool:
        """
        检查实体是否已存在于数据库中
        
        Args:
            entity_name: 实体名称
            
        Returns:
            是否存在
        """
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM knowledge_triples 
                    WHERE head_entity = %s OR tail_entity = %s
                """, (entity_name, entity_name))
                
                result = cursor.fetchone()
                return result["cnt"] > 0
        except Exception as e:
            logger.error(f"检查实体存在性失败: {e}")
            return False
    
    async def _add_new_entity(self, conn, entity: Dict[str, Any], update_stats: Dict[str, Any]):
        """
        添加新实体到知识图谱
        
        Args:
            conn: 数据库连接
            entity: 实体信息
            update_stats: 更新统计
        """
        cursor = conn.cursor()
        
        try:
            entity_name = entity["name"]
            entity_type = entity["type"] 
            
            # 1. 检查实体是否已存在
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM knowledge_triples 
                WHERE head_entity = %s OR tail_entity = %s
            """, (entity_name, entity_name))
            
            if cursor.fetchone()["cnt"] > 0:
                logger.info(f"实体 {entity_name} 已存在，跳过添加")
                return
            
            # 2. 为新实体寻找合适的关系
            entity_type_cn = self.entity_type_mapping.get(entity_type, "未知类型")
            
            # 添加实体类型关系
            cursor.execute("""
                INSERT INTO knowledge_triples (head_entity, relation, tail_entity)
                VALUES (%s, %s, %s)
            """, (entity_name, "属于", entity_type_cn))
            
            # 3. 根据特征添加更多关系
            features = entity.get("features", {})
            await self._add_feature_relations(cursor, entity_name, features)
            
            conn.commit()
            
            update_stats["new_entities_added"] += 1
            update_stats["updates"].append({
                "type": "new_entity",
                "entity": entity_name,
                "entity_type": entity_type,
                "confidence": entity["confidence"]
            })
            
            logger.info(f"成功添加新实体: {entity_name} ({entity_type})")
            
        except Exception as e:
            logger.error(f"添加实体失败: {e}")
            conn.rollback()
    
    async def _add_feature_relations(self, cursor, entity_name: str, features: Dict[str, Any]):
        """
        根据实体特征添加关系
        
        Args:
            cursor: 数据库游标
            entity_name: 实体名称
            features: 特征字典
        """
        # 颜色特征
        if "dominant_color" in features:
            color = features["dominant_color"]
            cursor.execute("""
                INSERT INTO knowledge_triples (head_entity, relation, tail_entity)
                VALUES (%s, %s, %s)
            """, (entity_name, "颜色", color))
        
        # 大小特征
        if "area" in features:
            area = features["area"]
            if area > 10000:
                size = "大型"
            elif area > 5000:
                size = "中等"
            else:
                size = "小型"
            
            cursor.execute("""
                INSERT INTO knowledge_triples (head_entity, relation, tail_entity)
                VALUES (%s, %s, %s)
            """, (entity_name, "大小", size))
        
        # 纹理特征
        if "texture_roughness" in features and features["texture_roughness"] > 100:
            cursor.execute("""
                INSERT INTO knowledge_triples (head_entity, relation, tail_entity)
                VALUES (%s, %s, %s)
            """, (entity_name, "纹理", "粗糙"))
    
    async def _process_entity_relationships(self, conn, detected_entities: List[Dict[str, Any]], update_stats: Dict[str, Any]):
        """
        处理多个实体间的关系
        
        Args:
            conn: 数据库连接
            detected_entities: 检测到的实体列表
            update_stats: 更新统计
        """
        cursor = conn.cursor()
        
        # 按类型分组
        insects = [e for e in detected_entities if e["type"] == "insect"]
        symptoms = [e for e in detected_entities if e["type"] == "disease_symptom"]
        trees = [e for e in detected_entities if e["type"] == "tree"]
        
        # 昆虫-症状关系（传播关系）
        for insect in insects:
            for symptom in symptoms:
                await self._add_relationship_if_not_exists(
                    cursor, 
                    insect["matched_kb_entity"] or insect["name"],
                    "传播",
                    symptom["matched_kb_entity"] or symptom["name"],
                    update_stats
                )
        
        # 树种-症状关系（易感关系）
        for tree in trees:
            for symptom in symptoms:
                await self._add_relationship_if_not_exists(
                    cursor,
                    tree["matched_kb_entity"] or tree["name"],
                    "易感",
                    symptom["matched_kb_entity"] or symptom["name"],
                    update_stats
                )
        
        # 昆虫-树种关系（寄主关系）
        for insect in insects:
            for tree in trees:
                await self._add_relationship_if_not_exists(
                    cursor,
                    insect["matched_kb_entity"] or insect["name"],
                    "寄主",
                    tree["matched_kb_entity"] or tree["name"],
                    update_stats
                )
        
        conn.commit()
    
    async def _add_relationship_if_not_exists(self, cursor, head_entity: str, relation: str, tail_entity: str, update_stats: Dict[str, Any]):
        """
        如果关系不存在，则添加关系
        
        Args:
            cursor: 数据库游标
            head_entity: 头实体
            relation: 关系
            tail_entity: 尾实体
            update_stats: 更新统计
        """
        # 检查关系是否已存在
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM knowledge_triples 
            WHERE head_entity = %s AND relation = %s AND tail_entity = %s
        """, (head_entity, relation, tail_entity))
        
        if cursor.fetchone()["cnt"] == 0:
            # 添加新关系
            cursor.execute("""
                INSERT INTO knowledge_triples (head_entity, relation, tail_entity)
                VALUES (%s, %s, %s)
            """, (head_entity, relation, tail_entity))
            
            update_stats["new_relations_added"] += 1
            update_stats["updates"].append({
                "type": "new_relation",
                "head_entity": head_entity,
                "relation": relation,
                "tail_entity": tail_entity
            })
            
            logger.info(f"添加新关系: {head_entity} --[{relation}]--> {tail_entity}")
    
    async def _discover_and_add_relationships(self, conn, detected_entities: List[Dict[str, Any]], update_stats: Dict[str, Any]):
        """
        通过AI推理发现新的关系
        
        Args:
            conn: 数据库连接
            detected_entities: 检测到的实体列表
            update_stats: 更新统计
        """
        from ai_service import get_kimi_service
        
        cursor = conn.cursor()
        kimi = get_kimi_service()
        
        # 获取有效关系列表
        cursor.execute("SELECT relation_name FROM valid_relations")
        valid_relations = [row["relation_name"] for row in cursor.fetchall()]
        
        if len(detected_entities) < 2 or not valid_relations:
            return
        
        # 对实体两两配对进行关系推理
        for i, entity_a in enumerate(detected_entities):
            for entity_b in detected_entities[i+1:]:
                name_a = entity_a["matched_kb_entity"] or entity_a["name"]
                name_b = entity_b["matched_kb_entity"] or entity_b["name"]
                
                # 检查是否已存在关系
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM knowledge_triples 
                    WHERE (head_entity = %s AND tail_entity = %s) 
                       OR (head_entity = %s AND tail_entity = %s)
                """, (name_a, name_b, name_b, name_a))
                
                if cursor.fetchone()["cnt"] == 0:
                    # 使用AI推理关系
                    try:
                        inferred_relation = kimi.infer_relation(name_a, name_b, valid_relations)
                        if inferred_relation and inferred_relation in valid_relations:
                            await self._add_relationship_if_not_exists(
                                cursor, name_a, inferred_relation, name_b, update_stats
                            )
                    except Exception as e:
                        logger.warning(f"关系推理失败: {name_a} <-> {name_b}, 错误: {e}")
        
        conn.commit()
    
    async def update_entity_features(self, entity_name: str, new_features: Dict[str, Any]) -> bool:
        """
        更新实体特征
        
        Args:
            entity_name: 实体名称
            new_features: 新特征
            
        Returns:
            是否更新成功
        """
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # 检查是否存在特征表（如果没有可以创建）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entity_features (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        entity_name VARCHAR(255) NOT NULL,
                        feature_type VARCHAR(100) NOT NULL,
                        feature_value TEXT,
                        confidence FLOAT DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_entity_name (entity_name)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 插入或更新特征
                for feature_type, feature_value in new_features.items():
                    # 检查特征是否已存在
                    cursor.execute("""
                        SELECT id FROM entity_features 
                        WHERE entity_name = %s AND feature_type = %s
                    """, (entity_name, feature_type))
                    
                    if cursor.fetchone():
                        # 更新现有特征
                        cursor.execute("""
                            UPDATE entity_features 
                            SET feature_value = %s 
                            WHERE entity_name = %s AND feature_type = %s
                        """, (json.dumps(feature_value), entity_name, feature_type))
                    else:
                        # 插入新特征
                        cursor.execute("""
                            INSERT INTO entity_features (entity_name, feature_type, feature_value)
                            VALUES (%s, %s, %s)
                        """, (entity_name, feature_type, json.dumps(feature_value)))
                
                conn.commit()
                logger.info(f"成功更新实体 {entity_name} 的特征")
                return True
                
        except Exception as e:
            logger.error(f"更新实体特征失败: {e}")
            return False
    
    async def get_knowledge_update_suggestions(self, detected_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        获取知识图谱更新建议
        
        Args:
            detected_entities: 检测到的实体列表
            
        Returns:
            更新建议列表
        """
        suggestions = []
        
        for entity in detected_entities:
            # 低相似度实体建议
            if entity["similarity"] < self.similarity_threshold and entity["confidence"] > self.confidence_threshold:
                suggestions.append({
                    "type": "add_entity",
                    "priority": "high",
                    "entity_name": entity["name"],
                    "entity_type": entity["type"],
                    "confidence": entity["confidence"],
                    "similarity": entity["similarity"],
                    "reason": f"检测到高置信度({entity['confidence']:.2f})但低相似度({entity['similarity']:.2f})的实体",
                    "action": f"建议将'{entity['name']}'添加为新的{entity['type']}实体"
                })
            
            # 特征更新建议
            if entity.get("matched_kb_entity") and entity["similarity"] > 0.7:
                suggestions.append({
                    "type": "update_features", 
                    "priority": "medium",
                    "entity_name": entity["matched_kb_entity"],
                    "new_features": entity.get("features", {}),
                    "reason": "检测到已知实体的新特征信息",
                    "action": f"建议更新'{entity['matched_kb_entity']}'的特征数据"
                })
        
        # 关系发现建议
        if len(detected_entities) > 1:
            suggestions.append({
                "type": "discover_relations",
                "priority": "medium",
                "entities": [e["matched_kb_entity"] or e["name"] for e in detected_entities],
                "reason": "图像中检测到多个实体，可能存在未知关系",
                "action": "建议分析实体间的潜在关系并添加到知识图谱"
            })
        
        return suggestions


# 全局服务实例
knowledge_graph_updater = None


def init_knowledge_updater(db_config: Dict[str, Any]):
    """
    初始化知识图谱更新器
    
    Args:
        db_config: 数据库配置
    """
    global knowledge_graph_updater
    
    knowledge_graph_updater = KnowledgeGraphUpdater(db_config)
    logger.info("知识图谱更新器初始化完成")


def get_knowledge_updater() -> KnowledgeGraphUpdater:
    """获取知识图谱更新器实例"""
    if knowledge_graph_updater is None:
        raise RuntimeError("知识图谱更新器未初始化")
    return knowledge_graph_updater