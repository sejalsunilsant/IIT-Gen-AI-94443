import pandas as pd

df=pd.read_csv("D:\Sunbeam\Files\products.csv")
print(df)
print("Number of rows:", len(df))
product_count =  len(df[df['price'] > 500])
print("Total number of products priced above 500:", product_count)
average_price = df['price'].mean()
print("Average price of all products:", average_price)
category = input("Enter category: ")
print(df[df['category'] == category])
print("Total quantity of all items in stock:", df['quantity'].sum())