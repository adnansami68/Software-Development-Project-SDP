#include <iostream>
#include <vector>
#include <string>
#include <iomanip>
#include <limits>
#include <fstream>
#include <cstdlib>
#include <algorithm>
#include <ctime>

using namespace std;

const string ACCOUNT_FILE = "bank_accounts.txt";
const string TRANSACTION_LOG = "bank_transactions.txt";
const string COUNTER_FILE = "account_counter.txt";
const int MIN_PASSWORD_LENGTH = 4;
const double SAVINGS_MIN_BALANCE = 100.0;
const double CURRENT_MIN_BALANCE = 500.0;

class BankAccount {
private:
    string accountNumber;
    string accountHolderName;
    string address;
    string phoneNumber;
    string email;
    double balance;
    string accountType;
    string password;
    vector<string> transactionHistory;

public:
    BankAccount(string accNum = "", string name = "", string addr = "", 
                string phone = "", string mail = "", double initialDeposit = 0.0, 
                string type = "Savings", string pwd = "1234")
        : accountNumber(accNum), accountHolderName(name), address(addr), 
          phoneNumber(phone), email(mail), balance(initialDeposit), 
          accountType(type), password(pwd) {
        if (initialDeposit > 0) {
            addTransaction("Account opened with initial deposit: " + to_string(initialDeposit) + " BDT");
        }
    }

    string getAccountNumber() const { 
        return accountNumber; 
    }
    string getAccountHolderName() const { 
        return accountHolderName; 
    }
    double getBalance() const { 
        return balance; 
    }
    string getAccountType() const {
        return accountType; 
    }
    string getPassword() const {
         return password;
    }
    const vector<string>& getTransactionHistory() const {
         return transactionHistory; 
    }

    void deposit(double amount) {
        if (amount > 0) {
            balance += amount;
            addTransaction("Deposit: +" + to_string(amount) + " BDT");
            cout << "Deposit successful. New balance: " << fixed << setprecision(2) << balance << " BDT" << endl;
        } else {
            cout << "Invalid deposit amount." << endl;
        }
    }

    bool verifyPassword(const string& pwd) const {
        return pwd == password;
    }

    void withdraw(double amount, const string& pwd) {
        if (!verifyPassword(pwd)) {
            cout << "Invalid password. Withdrawal failed." << endl;
            return;
        }

        if (amount <= 0) {
            cout << "Invalid withdrawal amount." << endl;
            return;
        }

        double minBalance = (accountType == "Savings") ? SAVINGS_MIN_BALANCE : CURRENT_MIN_BALANCE;
        
        if (balance - amount < minBalance) {
            cout << "Withdrawal failed. Minimum balance requirement not met." << endl;
            cout << "Minimum required balance for " << accountType << " account: " << minBalance << " BDT" << endl;
            return;
        }

        if (amount <= balance) {
            balance -= amount;
            addTransaction("Withdrawal: -" + to_string(amount) + " BDT");
            cout << "Withdrawal successful. New balance: " << fixed << setprecision(2) << balance << " BDT" << endl;
        } else {
            cout << "Insufficient funds." << endl;
        }
    }

    void displayAccountInfo() const {
        cout << "\n=== Account Information ===" << endl;
        cout << "Account Number: " << accountNumber << endl;
        cout << "Account Holder: " << accountHolderName << endl;
        cout << "Address: " << address << endl;
        cout << "Phone: " << phoneNumber << endl;
        cout << "Email: " << email << endl;
        cout << "Account Type: " << accountType << endl;
        cout << "Current Balance: " << fixed << setprecision(2) << balance << " BDT" << endl;
        cout << "===========================\n" << endl;
    }

    void displayTransactionHistory() const {
        cout << "\n=== Transaction History ===" << endl;
        cout << "Account: " << accountNumber << " (" << accountHolderName << ")" << endl;
        for (const auto& transaction : transactionHistory) {
            cout << "- " << transaction << endl;
        }
        cout << "===========================\n" << endl;
    }

    void saveToFile(ofstream& outFile) const {
        outFile << accountNumber << endl;
        outFile << accountHolderName << endl;
        outFile << address << endl;
        outFile << phoneNumber << endl;
        outFile << email << endl;
        outFile << fixed << setprecision(2) << balance << endl;
        outFile << accountType << endl;
        outFile << password << endl;
        
        outFile << transactionHistory.size() << endl;
        for (const auto& transaction : transactionHistory) {
            outFile << transaction << endl;
        }
    }


    void loadFromFile(ifstream& inFile) {
        getline(inFile, accountNumber);
        getline(inFile, accountHolderName);
        getline(inFile, address);
        getline(inFile, phoneNumber);
        getline(inFile, email);
        inFile >> balance;
        inFile.ignore();
        getline(inFile, accountType);
        getline(inFile, password);
    
        int transactionCount;
        inFile >> transactionCount;
        inFile.ignore();
        transactionHistory.clear();
        for (int i = 0; i < transactionCount; ++i) {
            string transaction;
            getline(inFile, transaction);
            transactionHistory.push_back(transaction);
        }
    }

private:
    void addTransaction(const string& description) {
        time_t now = time(0);
        string dt = ctime(&now);
        dt.erase(dt.find_last_not_of("\n") + 1); // Remove newline
        transactionHistory.push_back(dt + " - " + description);
    }
};

class BankingSystem {
private:
    vector<BankAccount> accounts;
    int accountCounter = 1000;
    string generateAccountNumber() {
        accountCounter++;
        return "ACCT" + to_string(accountCounter);
    }
    void loadAccountCounter() {
        ifstream inFile(COUNTER_FILE);
        if (inFile) {
            inFile >> accountCounter;
            inFile.close();
        }
    }
    void saveAccountCounter() {
        ofstream outFile(COUNTER_FILE);
        if (outFile) {
            outFile << accountCounter;
            outFile.close();
        }
    }

    BankAccount* findAccount(const string& accNum) {
        for (auto& account : accounts) {
            if (account.getAccountNumber() == accNum) {
                return &account;
            }
        }
        return nullptr;
    }

    void loadAccounts() {
        ifstream inFile(ACCOUNT_FILE);
        if (inFile) {
            while (inFile.peek() != EOF) {
                BankAccount account;
                account.loadFromFile(inFile);
                accounts.push_back(account);
                
                string accNum = account.getAccountNumber().substr(4);
                int num = stoi(accNum);
                if (num >= accountCounter) {
                    accountCounter = num;
                }
            }
            inFile.close();
        }
    }

    void saveAccounts() {
        ofstream outFile(ACCOUNT_FILE);
        if (outFile) {
            for (const auto& account : accounts) {
                account.saveToFile(outFile);
            }
            outFile.close();
        } else {
            cerr << "Error saving accounts to file!" << endl;
        }
    }

    void logTransaction(const string& message) {
        ofstream logFile(TRANSACTION_LOG, ios::app);
        if (logFile) {
            time_t now = time(0);
            logFile << ctime(&now) << " - " << message << "\n\n";
            logFile.close();
        }
    }

    void clearScreen() {
        #ifdef _WIN32
            system("cls");
        #else
            system("clear");
        #endif
    }

public:
    BankingSystem() {
        loadAccountCounter();
        loadAccounts();
    }

    ~BankingSystem() {
        saveAccounts();
        saveAccountCounter();
    }

    void createNewAccount() {
        string name, address, phone, email, accountType, password;
        double initialDeposit;

        clearScreen();
        cout << "\n=== Create New Account ===" << endl;

        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        while (true) {
            cout << "Enter full name: ";
            getline(cin, name);
            if (!name.empty()) break;
            cout << "Name cannot be empty. Please try again." << endl;
        }

        while (true) {
            cout << "Enter address: ";
            getline(cin, address);
            if (!address.empty()) break;
            cout << "Address cannot be empty. Please try again." << endl;
        }
        while (true) {
            cout << "Enter phone number: ";
            getline(cin, phone);
            if (all_of(phone.begin(), phone.end(), ::isdigit)) break;
            cout << "Phone number must contain only digits. Please try again." << endl;
        }

        while (true) {
            cout << "Enter email: ";
            getline(cin, email);
            if (email.find('@') != string::npos && email.find('.') != string::npos) break;
            cout << "Invalid email format. Please try again." << endl;
        }

        while (true) {
            cout << "Enter account type (Savings/Current): ";
            getline(cin, accountType);
            if (accountType == "Savings" || accountType == "Current") {
                break;
            }
            cout << "Invalid account type. Please enter 'Savings' or 'Current'." << endl;
        }

        double minDeposit = (accountType == "Savings") ? SAVINGS_MIN_BALANCE : CURRENT_MIN_BALANCE;
        while (true) {
            cout << "Enter initial deposit amount (minimum " << minDeposit << " BDT): ";
            if (cin >> initialDeposit) {
                if (initialDeposit >= minDeposit) {
                    cin.ignore();
                    break;
                }
                cout << "Minimum deposit for " << accountType << " account is " << minDeposit << " BDT" << endl;
            } else {
                cout << "Invalid amount. Please enter a numeric value." << endl;
                cin.clear();
                cin.ignore(numeric_limits<streamsize>::max(), '\n');
            }
        }

        cout << "Set a " << MIN_PASSWORD_LENGTH << "-digit password for withdrawals: ";
        cin>>password;
        while (password.length() != MIN_PASSWORD_LENGTH || !all_of(password.begin(), password.end(), ::isdigit)) {
            cout << "\nPassword must be " << MIN_PASSWORD_LENGTH << " digits. Please try again: ";
            cin>>password;
        }

        string accNum = generateAccountNumber();
        accounts.emplace_back(accNum, name, address, phone, email, initialDeposit, accountType, password);

        string successMsg = "Account created: " + accNum + " for " + name;
        cout << "\n\n" << successMsg << endl;
        logTransaction(successMsg);

        cout << "\n=== Account Created Successfully ===" << endl;
        cout << "Account Number: " << accNum << endl;
        cout << "Account Holder: " << name << endl;
        cout << "Account Type: " << accountType << endl;
        cout << "Initial Balance: " << fixed << setprecision(2) << initialDeposit << " BDT" << endl;
        cout << "==================================\n" << endl;
    }

    void depositMoney() {
        string accNum;
        double amount;

        clearScreen();
        cout << "\n=== Deposit Money ===" << endl;
        cout << "Enter account number: ";
        cin >> accNum;

        BankAccount* account = findAccount(accNum);
        if (account) {
            cout << "Account holder: " << account->getAccountHolderName() << endl;
            cout << "Current balance: " << fixed << setprecision(2) << account->getBalance() << " BDT" << endl;
            
            while (true) {
                cout << "Enter deposit amount: ";
                if (cin >> amount) {
                    account->deposit(amount);
                    logTransaction("Deposit to " + accNum + ": " + to_string(amount) + " BDT");
                    saveAccounts();
                    break;
                } else {
                    cout << "Invalid amount. Please enter a numeric value." << endl;
                    cin.clear();
                    cin.ignore(numeric_limits<streamsize>::max(), '\n');
                }
            }
        } else {
            cout << "Account not found." << endl;
        }
    }

    void withdrawMoney() {
        string accNum, password;
        double amount;

        clearScreen();
        cout << "\n=== Withdraw Money ===" << endl;
        cout << "Enter account number: ";
        cin >> accNum;

        BankAccount* account = findAccount(accNum);
        if (account) {
            cout << "Account holder: " << account->getAccountHolderName() << endl;
            cout << "Current balance: " << fixed << setprecision(2) << account->getBalance() << " BDT" << endl;
            
            cout << "Enter your " << MIN_PASSWORD_LENGTH << "-digit password: ";
            cin.ignore();
            cin>> password;
            cout << endl;

            while (true) {
                cout << "Enter withdrawal amount: ";
                if (cin >> amount) {
                    account->withdraw(amount, password);
                    if (amount > 0 && amount <= account->getBalance() && account->verifyPassword(password)) {
                        logTransaction("Withdrawal from " + accNum + ": " + to_string(amount) + " BDT");
                        saveAccounts();
                    }
                    break;
                } else {
                    cout << "Invalid amount. Please enter a numeric value." << endl;
                    cin.clear();
                    cin.ignore(numeric_limits<streamsize>::max(), '\n');
                }
            }
        } else {
            cout << "Account not found." << endl;
        }
    }

    void checkBalance() {
        string accNum;

        clearScreen();
        cout << "\n=== Check Balance ===" << endl;
        cout << "Enter account number: ";
        cin >> accNum;

        BankAccount* account = findAccount(accNum);
        if (account) {
            cout << "Account holder: " << account->getAccountHolderName() << endl;
            cout << "Account type: " << account->getAccountType() << endl;
            cout << "Current balance: " << fixed << setprecision(2) << account->getBalance() << " BDT" << endl;
        } else {
            cout << "Account not found." << endl;
        }
    }

    void displayAccountDetails() {
        string accNum;

        clearScreen();
        cout << "\n=== Account Details ===" << endl;
        cout << "Enter account number: ";
        cin >> accNum;

        BankAccount* account = findAccount(accNum);
        if (account) {
            account->displayAccountInfo();
        } else {
            cout << "Account not found." << endl;
        }
    }

    void viewTransactionHistory() {
        string accNum;

        clearScreen();
        cout << "\n=== Transaction History ===" << endl;
        cout << "Enter account number: ";
        cin >> accNum;

        BankAccount* account = findAccount(accNum);
        if (account) {
            account->displayTransactionHistory();
        } else {
            cout << "Account not found." << endl;
        }
    }

    void displayAllAccounts() {
        clearScreen();
        cout<<"Enter Admin Password:";
        string admin_pass;
        cin>>admin_pass;
        if(admin_pass=="2255"){
            cout << "\n=== All Accounts ===" << endl;
            if (accounts.empty()) {
                cout << "No accounts found." << endl;
            } else {
                for (const auto& account : accounts) {
                    cout << "Account Number: " << account.getAccountNumber() 
                            << " | Holder: " << account.getAccountHolderName()
                            << " | Type: " << account.getAccountType()
                            << " | Balance: " << fixed << setprecision(2) << account.getBalance() << " BDT" << endl;
                }
            }
            cout << "=====================\n" << endl;
        }
        else{
            cout<<"\nInvalid Pass"<<endl;
            return;
        }
    }
};

void displayMenu() {
    cout << "\n=== Banking System Menu ===" << endl;
    cout << "1. Create New Account" << endl;
    cout << "2. Deposit Money" << endl;
    cout << "3. Withdraw Money" << endl;
    cout << "4. Check Balance" << endl;
    cout << "5. Display Account Details" << endl;
    cout << "6. View Transaction History" << endl;
    cout << "7. View All Accounts" << endl;
    cout << "8. Exit" << endl;
    cout << "==========================" << endl;
    cout << "Enter your choice (1-8): ";
}

int main() {
    BankingSystem bank;
    int choice;

    cout << "Welcome to the Banking System" << endl;

    while (true) {
        displayMenu();
        
        if (!(cin >> choice)) {
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "Invalid input. Please enter a number between 1 and 8." << endl;
            continue;
        }

        switch (choice) {
            case 1:
                bank.createNewAccount();
                break;
            case 2:
                bank.depositMoney();
                break;
            case 3:
                bank.withdrawMoney();
                break;
            case 4:
                bank.checkBalance();
                break;
            case 5:
                bank.displayAccountDetails();
                break;
            case 6:
                bank.viewTransactionHistory();
                break;
            case 7:
                bank.displayAllAccounts();
                break;
            case 8:
                cout << "Thank you for using our Banking System. Goodbye!" << endl;
                return 0;
            default:
                cout << "Invalid choice. Please enter a number between 1 and 8." << endl;
        }

        cout << "\nPress Enter to continue...";
        cin.ignore();
        cin.get();
    }

    return 0;
}
