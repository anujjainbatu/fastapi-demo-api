from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="The unique identifier for the patient", example="P001")]
    name: Annotated[str, Field(..., description="The name of the patient", example="John Doe")]
    city: Annotated[str, Field(..., description="The city where the patient resides", example="New York")]
    age: Annotated[int, Field(..., description="The age of the patient", example=30)]
    gender: Annotated[Literal['male','female','other'], Field(..., description="The gender of the patient")]
    height: Annotated[float, Field(..., description="The height of the patient in meters", example=1.55)]
    weight: Annotated[float, Field(..., description="The weight of the patient in kilograms", example=70.0)]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"
        
class PatientUpdate(BaseModel):
    id: Annotated[Optional[str], Field(None, description="The unique identifier for the patient", example="P001")]
    name: Annotated[Optional[str], Field(None, description="The name of the patient", example="John Doe")]
    city: Annotated[Optional[str], Field(None, description="The city where the patient resides", example="New York")]
    age: Annotated[Optional[int], Field(None, description="The age of the patient", example=30)]
    gender: Annotated[Optional[Literal['male','female','other']], Field(None, description="The gender of the patient")]
    height: Annotated[Optional[float], Field(None, description="The height of the patient in meters", example=1.55)]
    weight: Annotated[Optional[float], Field(None, description="The weight of the patient in kilograms", example=70.0)]    

def load_data():
    with open("patients.json", "r") as file:
        data = json.load(file)

    return data

def save_data(data):
    with open("patients.json", "w") as file:
        json.dump(data, file)

@app.get("/")
def read_root():
    return {"message": "Patient Management System API"}

@app.get("/about")
def read_about():
    return {
        "name": "Patient Management System API",
        "version": "1.0.0",
        "description": "API for managing patient records, appointments, and medical history."
    }

@app.get("/view")
def view_patients():
    data = load_data()
    return data

@app.get("/patient/{patient_id}")
def view_patient(patient_id: str = Path(..., description="The ID of the patient to view", example="P001")):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/sort")
def sort_patients(sort_by: str = Query(..., description="Sort patients by 'name' or 'id'", example="name"), order: str = Query('asc', description="Order of sorting: 'asc' or 'desc'", example="asc")):
    valid_sort_fields = ['height', 'weight', 'bmi', 'age']
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}. Valid fields are: {', '.join(valid_sort_fields)}")
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Order must be 'asc' or 'desc'")
    
    data = load_data()
    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=(order == 'desc'))
    return sorted_data

@app.post("/create")
def create_patient(patient: Patient):
    
    # load existing data
    data = load_data()

    # check if patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    
    # new patient add to database
    data[patient.id] = patient.model_dump(exclude=['id'])

    # save into json file
    save_data(data)

    return JSONResponse(status_code=201, content={"message": "Patient created successfully", "patient": patient})

@app.put("/edit/{patient_id}")
def edit_patient(patient_id: str, patient_update: PatientUpdate):
    # load existing data
    data = load_data()

    # check if patient exists
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # update patient details
    existing_patient = data[patient_id]
    updated_patient = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_patient.items():
        existing_patient[key] = value

    #existing_patient -> pydantic object -> updated bmi and verdict
    existing_patient['id'] = patient_id  # Ensure the ID remains unchanged
    existing_patient_obj = Patient(**existing_patient)

    # pydantic object to dict
    existing_patient = existing_patient_obj.model_dump(exclude=['id'])

    # add this updated patient back to data
    data[patient_id] = existing_patient

    # save into json file
    save_data(data)
    return JSONResponse(status_code=200, content={'message':'patient updated'})

@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    # load existing data
    data = load_data()

    # check if patient exists
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # delete patient from data
    del data[patient_id]

    # save into json file
    save_data(data)

    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully"})