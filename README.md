# negation_vllm
## stages
- negation dataset construction
- experiment with model learning mask

## note
- dataset_construction is only for the VQA v2 maybe
- counting the TASKNUM ADND TASK ITER
    - TASKNUM can set up to 100
    - TASKITER = total length of dataset / TASKNUM


## to do 
- modify the dataset_construction to make sure the imageid can be mapped correctly
- balanced the correct answer label when constructing the dataset
- check the data in different datasets to improve the diversity in our VQA dataset