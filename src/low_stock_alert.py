import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import openpyxl
import pandas as pd

#to read the excel file
df = pd.read_excel(
    r"data/inventory_data.xlsx"
)
print(df.head())

low_stock = df["CurrentStock"] <= df["ReorderLevel"]
print(low_stock)

# Create stock status
df["Status"] = df.apply(
    lambda row: "LOW STOCK"
    if row["CurrentStock"] <= row["ReorderLevel"]
    else "NORMAL",
    axis=1,
)
print(df["Status"])

# Calculate target stock, quantity, and cost
df["TargetStock"] = df["ReorderLevel"] * 2
df["ReorderQuantity"] = (df["TargetStock"] - df["CurrentStock"]).clip(lower=0)
print(df["ReorderQuantity"])

df["ReorderCost"] = df["ReorderQuantity"] * df["UnitCost"]
print(df["ReorderCost"])

# to generate the report and construct the message
report = df[df["Status"] == "LOW STOCK"][
    [
        "ProductID",
        "Product",
        "Category",
        "CurrentStock",
        "ReorderLevel",
        "ReorderQuantity",
        "UnitCost",
        "ReorderCost",
        "Supplier",
    ]
]

report.to_excel("output/low_stock_report.xlsx", index=False)
print("Report Successfully Generated")

if len(report) > 0:
    message = "LOW STOCK ALERT\n\n"
    for _, row in report.iterrows():
        message += (
            f"• {row['Product']} → {row['CurrentStock']} remaining "
            f"(Reorder Level: {row['ReorderLevel']}) | "
            f"Order Qty: {row['ReorderQuantity']} | "
            f"Cost: ${row['ReorderCost']:.2f}\n"
        )
else:
    message = "All products have sufficient stock."

# Terminal alerts
print("=" * 45)
print(" LOW STOCK ALERT")
print("=" * 45)
print(message)
print("=" * 45)
print(f"{len(report)} products require replenishment.")
print("=" * 45)


# email automation 
def send_email_alert(alert_content):
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Daily Inventory Low Stock Alert"

    msg.attach(MIMEText(alert_content, "plain"))

    server = None  # Safe baseline Initialization

    try:
        print("Connecting to email server...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email alert sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(
            "Check: Are you connected to the internet? Is a firewall/VPN blocking port 587?"
        )
    finally:
        if server is not None:
            server.quit()


# to trigger email alert
if len(report) > 0:
    send_email_alert(message)
