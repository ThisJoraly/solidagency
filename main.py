from web3 import Web3
import re
from web3.middleware import geth_poa_middleware
from contr import abi, contract_address

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

contract = w3.eth.contract(address=contract_address, abi=abi)

def validate_password(password):
    if len(password) < 12:
        return False, "Пароль должен быть не менее 12 символов"
    if not re.search("[a-z]", password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"
    if not re.search("[A-Z]", password):
        return False, "Пароль должен содержать хотя бы одну прописную букву"
    if not re.search("[0-9]", password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Пароль должен содержать хотя бы один специальный символ"
    if re.fullmatch(r"(password123|qwerty123)", password):
        return False, "Избегайте простых и общеизвестных паролей"
    return True, ""

def register():
    password = input("Введите пароль: ")
    valid, message = validate_password(password)
    match valid:
        case False:
            print(message)
        case True:
            try:
                account = w3.geth.personal.new_account(password)
                print(f"Публичный ключ: {account}")
            except Exception as e:
                print(f"Ошибка регистрации: {e}")

def login():
    public_key = input("Введите ключ: ")
    password = input("Введите пароль: ")
    try:
        w3.geth.personal.unlock_account(public_key, password, 300)
        print("Авторизация прошла успешно")
        return public_key
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        return None

def create_estate(account):
    address_estate = input("Введите адрес недвижимости: ")
    square = int(input("Введите площадь в квадратных метрах: "))
    match square:
        case square if square <= 2:
            print("Площадь недвижимости должна быть больше 2 кв.м")
            return
    es_type = int(input("Введите тип недвижимости (0-House, 1-Flat, 2-Loft, 3-Dacha): "))
    try:
        tx_hash = contract.functions.createEstate(address_estate, square, es_type).transact({'from': account})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Транзакция создания недвижимости подтверждена: {receipt.transactionHash.hex()}")
    except Exception as e:
        print(f"Ошибка создания недвижимости: {e}")

def change_estate_status(account):
    estate_id = int(input("Введите ID недвижимости: "))
    is_active = input("Активна недвижимость? (да/нет): ").lower() == 'да'
    try:
        tx_hash = contract.functions.updateEstateActive(estate_id, is_active).transact({'from': account})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Транзакция изменения статуса недвижимости подтверждена: {receipt.transactionHash.hex()}")
    except Exception as e:
        print(f"Ошибка изменения статуса недвижимости: {e}")

def create_advertisement(account):
    estate_id = int(input("Введите ID недвижимости для объявления: "))
    price = float(input("Введите цену в эфирах: "))
    match price:
        case price if price <= 0:
            print("Цена должна быть больше нуля")
            return
    try:
        tx_hash = contract.functions.createAd(estate_id, int(price * 10 ** 18)).transact({'from': account})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Транзакция создания объявления подтверждена: {receipt.transactionHash.hex()}")
    except Exception as e:
        print(f"Ошибка создания объявления: {e}")

def change_ad_status(account):
    ad_id = int(input("Введите ID объявления: "))
    new_status = int(input("Введите новый статус объявления (0-Opened, 1-Closed): "))
    try:
        tx_hash = contract.functions.updateAdType(ad_id, new_status).transact({'from': account})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Транзакция изменения статуса объявления подтверждена: {receipt.transactionHash.hex()}")
    except Exception as e:
        print(f"Ошибка изменения статуса объявления: {e}")

def buy_estate(account):
    ad_id = int(input("Введите ID объявления для покупки: "))
    try:
        ad = contract.functions.ads(ad_id).call()
        ad_price = ad[0]  # price is the first element in the returned tuple
        tx_hash = contract.functions.buyEstate(ad_id).transact({'from': account, 'value': ad_price})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Транзакция покупки недвижимости подтверждена: {receipt.transactionHash.hex()}")
    except Exception as e:
        match str(e):
            case "insufficient funds":
                print("Недостаточно средств для покупки")
            case _:
                print(f"Ошибка покупки недвижимости: {e}")

def withdraw_funds(account):
    amount = float(input("Введите сумму для вывода в эфирах: "))
    match amount:
        case amount if amount <= 0:
            print("Сумма должна быть больше нуля")
            return
    try:
        tx_hash = contract.functions.withdraw(Web3.toWei(amount, 'ether')).transact({'from': account})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Транзакция вывода средств подтверждена: {receipt.transactionHash.hex()}")
    except Exception as e:
        match str(e):
            case "no funds to withdraw":
                print("Нет средств для вывода")
            case _:
                print(f"Ошибка вывода средств: {e}")

def get_balance_on_contract(account):
    try:
        balance = contract.functions.getBalance().call({'from': account})
        print(f"Ваш баланс на смарт-контракте: {Web3.fromWei(balance, 'ether')} ether")
    except Exception as e:
        print(f"Ошибка получения информации о балансе: {e}")

def get_estates(account):
    try:
        estates = contract.functions.getEstates().call({'from': account})
        if not estates:
            print("Нет доступных недвижимостей.")
        else:
            for estate in estates:
                print(f"ID: {estate['estateId']}, Адрес: {estate['addressEstate']}, Площадь: {estate['square']} кв.м, Тип: {estate['esType']}, Владелец: {estate['owner']}, Активна: {'Да' if estate['isActive'] else 'Нет'}")
    except Exception as e:
        print(f"Ошибка получения списка недвижимостей: {e}")

def get_ads(account):
    try:
        ads = contract.functions.getAds().call({'from': account})
        if not ads:
            print("Нет доступных объявлений.")
        else:
            for ad in ads:
                print(f"ID объявления: {ad['adId']}, Цена: {Web3.fromWei(ad['price'], 'ether')} ether, ID недвижимости: {ad['estateId']}, Владелец: {ad['owner']}, Покупатель: {ad['buyer']}, Статус: {'Открыто' if ad['adType'] == 0 else 'Закрыто'}")
    except Exception as e:
        print(f"Ошибка получения списка объявлений: {e}")

def main():
    account = ""
    is_auth = False
    while True:
        if not is_auth:
            choice = input("Введите:\n1. Авторизация\n2. Регистрация\n3. Выход\n")
            match choice:
                case "1":
                    account = login()
                    if account:
                        is_auth = True
                case "2":
                    register()
                case "3":
                    break
                case _:
                    print("Введите 1, 2 или 3")
        else:
            choice = input("Введите:\n1. Создать недвижимость\n2. Изменить статус недвижимости\n3. Создать объявление\n4. Изменить статус объявления\n5. Купить недвижимость\n6. Посмотреть информацию\n7. Посмотреть баланс аккаунта\n8. Вывести средства\n9. Выйти из аккаунта\n")
            match choice:
                case "1":
                    create_estate(account)
                case "2":
                    change_estate_status(account)
                case "3":
                    create_advertisement(account)
                case "4":
                    change_ad_status(account)
                case "5":
                    buy_estate(account)
                case "6":
                    sub_choice = input("Введите:\n1. Посмотреть баланс на смарт-контракте\n2. Посмотреть доступные недвижимости\n3. Посмотреть текущие объявления\n")
                    match sub_choice:
                        case "1":
                            get_balance_on_contract(account)
                        case "2":
                            get_estates(account)
                        case "3":
                            get_ads(account)
                        case _:
                            print("Введите число от 1 до 3")
                case "7":
                    print(w3.eth.get_balance(account))
                case "8":
                    withdraw_funds(account)
                case "9":
                    is_auth = False
                case _:
                    print("Введите число от 1 до 9")

if __name__ == "__main__":
    main()
