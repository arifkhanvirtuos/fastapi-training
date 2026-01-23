age = 16



#with type annotation
age_typed:int = 16


def age_function(age_accepted:int)->int:
    return age_accepted


print("Age with type annotation:", age_function.__annotations__)

#common built-in types
int, float, str, bool, list, dict, tuple

from typing import List, Dict, Tuple, Optional, Union, Annotated
from enum import Enum
age_annotated : Annotated[int, "This is an age < 90 otherwise the code will not run "]= 16


def annotated_function(age_param: Annotated[Optional[int], "This is an optional age parameter"] = 16) -> Dict[str, Union[int, str]]:
    if age_param is None:
        return {"age": "Not provided"}
    return {"age": age_param}



print("Annotated function output:", annotated_function.__annotations__)




class ModelNameEnum(str, Enum):
    alexNet = "alexnedsdsdst"
    resNet = "resnet"
    lenet = "lenet"

class categoriesEnum(str, Enum):
    cat = "cat"
    dog = "dog"
    rabbit = "rabbit"

def get_model_name(model_name: ModelNameEnum) -> str:
    return f"Model selected: {model_name}"


def common_function(category: categoriesEnum) -> str:
    return f"Category selected: {category}"

