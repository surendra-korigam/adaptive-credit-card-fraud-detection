from monitor.ml import train
if __name__ == "__main__":
    print("Training on Kaggle ULB creditcard.csv ...")
    result=train()
    print("\nEvaluation on held-out 20%:")
    for key,value in result.items(): print(f"{key}: {value}")
