from typing import List, Optional
from sqlalchemy.orm import Session
from core.database.models import NeuralModel, ModelFormat, ModelType

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
        return self.session.query(NeuralModel).filter(NeuralModel.id == model_id).first()

    def get_model_types(self) -> List[str]:
        result = self.session.query(ModelType.name).all()
        return result
    
    def get_model_formats(self) -> List[str]:
        result = self.session.query(ModelFormat.name).all()
        return result
    
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
        return self.session.query(NeuralModel).all()
    # def get_by_id_with_details(self, model_id: int) -> Optional[dict]:
    #     """Получает полную информацию о модели"""
    #     result = (self.session.query(
    #                 NeuralModel,
    #                 ModelType.name.label('model_type'),
    #                 ModelFormat.name.label('format')
    #              )
    #              .join(ModelType, NeuralModel.model_type_id == ModelType.id)
    #              .join(ModelFormat, NeuralModel.format_id == ModelFormat.id)
    #              .filter(NeuralModel.id == model_id)
    #              .first())
        
    #     if result:
    #         neural_model, model_type, format_name = result
    #         return {
    #             'id': neural_model.id,
    #             'name': neural_model.name,
    #             'original_path': neural_model.original_path,
    #             'model_type': model_type,
    #             'format': format_name,
    #             'size': neural_model.size
    #         }
    #     return None
    
    # def get_models_by_type_name(self, type_name: str) -> List[NeuralModel]:
    #     """Получить модели по названию типа"""
    #     return (self.session.query(NeuralModel)
    #             .join(ModelType, NeuralModel.model_type_id == ModelType.id)
    #             .filter(ModelType.name == type_name)
    #             .all())