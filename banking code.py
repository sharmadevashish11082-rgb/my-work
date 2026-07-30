# Banking System in Python
# Works in IDLE without external libraries

import json
import os

FILE_NAME = "accounts.json"


# Load accounts from file
def load_accounts():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    return {}


# Save accounts to file
def save_accounts(accounts):
    with open(FILE_NAME, "w") as file:
        json.dump(accounts, file, indent=4)


# Create account
def create_account(accounts):
    acc_no = input("Enter Account Number: ")

    if acc_no in accounts:
        print("Account already exists!")
        return

    name = input("Enter Account Holder Name: ")
    balance = float(input("Enter Initial Deposit: "))

    accounts[acc_no] = {
        "name": name,
        "balance": balance
    }

    save_accounts(accounts)
    print("Account Created Successfully!")


# Deposit money
def deposit(accounts):
    acc_no = input("Enter Account Number: ")

    if acc_no not in accounts:
        print("Account not found!")
        return

    amount = float(input("Enter Amount to Deposit: "))
    accounts[acc_no]["balance"] += amount

    save_accounts(accounts)
    print("Deposit Successful!")
    print("New Balance:", accounts[acc_no]["balance"])


# Withdraw money
def withdraw(accounts):
    acc_no = input("Enter Account Number: ")

    if acc_no not in accounts:
        print("Account not found!")
        return

    amount = float(input("Enter Amount to Withdraw: "))

    if amount > accounts[acc_no]["balance"]:
        print("Insufficient Balance!")
    else:
        accounts[acc_no]["balance"] -= amount
        save_accounts(accounts)
        print("Withdrawal Successful!")
        print("Remaining Balance:", accounts[acc_no]["balance"])


# Check balance
def check_balance(accounts):
    acc_no = input("Enter Account Number: ")

    if acc_no not in accounts:
        print("Account not found!")
        return

    print("\nAccount Details")
    print("----------------")
    print("Name:", accounts[acc_no]["name"])
    print("Balance:", accounts[acc_no]["balance"])


# View all accounts
def view_accounts(accounts):
    if not accounts:
        print("No accounts found.")
        return

    print("\nAll Accounts")
    print("-" * 40)

    for acc_no, details in accounts.items():
        print(f"Account No: {acc_no}")
        print(f"Name      : {details['name']}")
        print(f"Balance   : ₹{details['balance']}")
        print("-" * 40)


# Main program
def main():
    accounts = load_accounts()

    while True:
        print("\n===== BANKING SYSTEM =====")
        print("1. Create Account")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Check Balance")
        print("5. View All Accounts")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            create_account(accounts)

        elif choice == "2":
            deposit(accounts)

        elif choice == "3":
            withdraw(accounts)

        elif choice == "4":
            check_balance(accounts)

        elif choice == "5":
            view_accounts(accounts)

        elif choice == "6":
            print("Thank you for using the Banking System!")
            break

        else:
            print("Invalid Choice! Try Again.")


if __name__ == "__main__":
    main()
