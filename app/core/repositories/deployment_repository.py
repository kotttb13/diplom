from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from core.database.models import DeploymentRecord, OptimizedModel, Device


class DeploymentRepository:
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, deployment: DeploymentRecord) -> DeploymentRecord:
            self.session.add(deployment)
            self.session.commit()
            
    
    def create_deployment(
        self, 
        optimized_model_id: int,
        device_id: int,
        status: str = "pending"
    ) -> DeploymentRecord:
        deployment = DeploymentRecord(
            optimized_model_id=optimized_model_id,
            device_id=device_id,
            deployment_date=datetime.utcnow(),
            status=status
        )
        self.save(deployment)
        return deployment
    
    def update_status(self, deployment_id: int, status: str) -> DeploymentRecord:

        deployment = self.get_by_id(deployment_id)
        if deployment:
            deployment.status = status
            deployment.deployment_date = datetime.utcnow()
            return self.save(deployment)
        return None
    
    def get_by_id(self, deployment_id: int) -> Optional[DeploymentRecord]:

        return self.session.query(DeploymentRecord).filter(
            DeploymentRecord.id == deployment_id
        ).first()
    
   
    def get_all(self) -> List[DeploymentRecord]:
        """Получение всех записей развертывания"""
        return self.session.query(DeploymentRecord).order_by(
            desc(DeploymentRecord.deployment_date)
        ).all()
    
    def delete(self, deployment_id: int) -> bool:
        """Удаление записи развертывания"""
        deployment = self.get_by_id(deployment_id)
        if deployment:
            self.session.delete(deployment)
            self.session.commit()
            return True
        return False
    
