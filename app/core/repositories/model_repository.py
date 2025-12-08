from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from core.database.models import NeuralModel, ModelFormat, ModelType
from datetime import datetime

class ModelRepository:
    def __init__(self, session: Session):
        self.session = session
    def save(self, model: NeuralModel) -> None:
        self.session.add(model)
        self.session.commit()

    def get_model_type_and_format(self, model_id: int) -> Optional[dict]:
        result = (self.session.query(
                    ModelType.name.label('model_type_name'), 
                    ModelFormat.name.label('format_name')  
                 )
                 .select_from(NeuralModel)
                 .join(ModelType, NeuralModel.type_id == ModelType.id) 
                 .join(ModelFormat, NeuralModel.format_id == ModelFormat.id)      
                 .filter(NeuralModel.id == model_id)
                 .first())
        
        if result:
            return {
                'model_type': result.model_type_name.lower(),
                'model_format': result.format_name.lower()
            }
        return None
    
    def get_by_id(self, model_id: int) -> Optional[NeuralModel]:
         return (self.session.query(NeuralModel)
                .options(
                    joinedload(NeuralModel.type_neural_model),    
                    joinedload(NeuralModel.format_neural_model)
                )
                .filter(NeuralModel.id == model_id)
                .first())
    

    def get_model_types(self) -> List[str]:
        result = self.session.query(ModelType.name).all()
        return [row[0] for row in result] if result else []
    
    def get_model_formats(self) -> List[str]:
        result = self.session.query(ModelFormat.name).all()
        return [row[0] for row in result] if result else []
    
    def create_model(self, name: str, original_path: str, model_type_name: str, 
                   format_name: str, size: float = None) -> NeuralModel:
        
        model_type = self.session.query(ModelType).filter(
            ModelType.name == model_type_name
        ).first()
        if not model_type:
            raise ValueError(f"Неизвестный тип модели: {model_type_name}")
        
        model_format = self.session.query(ModelFormat).filter(
            ModelFormat.name == format_name
        ).first()
        if not model_format:
            raise ValueError(f"Неизвестный формат: {format_name}")
        
        model = NeuralModel(
            name=name,
            original_path=original_path,
            type_id=model_type.id,
            format_id=model_format.id,
            size=size
        )
        
        self.save(model)
        return model
    
    def get_format_by_id(self, model_id):
        result = (self.session.query( 
                    ModelFormat.name.label('format_name')  
                 )
                 .select_from(NeuralModel)
                 .join(ModelFormat, NeuralModel.format_id == ModelFormat.id)      
                 .filter(NeuralModel.id == model_id)
                 .first())
        
        if result:
            return {
                'model_format': result.format_name.lower()
            }
        return None
    
    def get_path_by_id(self, model_id):
        return self.session.query(NeuralModel.original_path).filter(NeuralModel.id == model_id).first()
    
    def get_all(self) -> List[NeuralModel]:
        return (self.session.query(NeuralModel)
                .options(
                    joinedload(NeuralModel.type_neural_model),    
                    joinedload(NeuralModel.format_neural_model)
                )
                .order_by(NeuralModel.id.desc())
                .all())
    
    def delete(self, model_id: int) -> bool:
        """Удалить модель по ID"""
        try:
            model = self.get_by_id(model_id)
            if model:
                self.session.delete(model)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise e
        
    def update(self, model_id: int, **kwargs) -> Optional[NeuralModel]:
   
        try:
            model = self.get_by_id(model_id)
            if not model:
                return None
            
            for key, value in kwargs.items():
                if hasattr(model, key):
                    setattr(model, key, value)
            
            if 'type_name' in kwargs:
                model_type = self.session.query(ModelType).filter(
                    ModelType.name == kwargs['type_name']
                ).first()
                if model_type:
                    model.type_id = model_type.id
            
            if 'format_name' in kwargs:
                model_format = self.session.query(ModelFormat).filter(
                    ModelFormat.name == kwargs['format_name']
                ).first()
                if model_format:
                    model.format_id = model_format.id
            
            model.updated_at = datetime.now()
            self.session.commit()
            return model
        except Exception as e:
            self.session.rollback()
            raise e 