import requests
import time
import json

def check_card_key(card):
    """检查单个卡密的可用性"""
    url = f"https://api.ow521.com/api/card-keys/{card}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        return {"available": False, "error": f"网络请求错误: {str(e)}"}
    except json.JSONDecodeError:
        return {"available": False, "error": "响应格式错误"}

def check_all_cards():
    """检查所有卡密"""
    try:
        # 读取卡密文件
        with open('card.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        cards = []
        for line in lines:
            line = line.strip()
            if line:
                # 移除行号前缀，只保留卡密
                if '→' in line:
                    card = line.split('→', 1)[1].strip()
                else:
                    card = line.strip()
                cards.append(card)

        print(f"开始检查 {len(cards)} 个卡密...")
        print("-" * 60)

        available_cards = []
        unavailable_cards = []

        for i, card in enumerate(cards, 1):
            print(f"[{i}/{len(cards)}] 检查卡密: {card}")

            result = check_card_key(card)

            if result.get("available", False):
                print(f"  [OK] 可用")
                available_cards.append(card)
            else:
                error_msg = result.get("error", "未知错误")
                print(f"  [FAIL] 不可用 - {error_msg}")
                unavailable_cards.append({"card": card, "error": error_msg})

            # 添加延迟避免请求过于频繁
            if i < len(cards):
                time.sleep(0.1)

        print("-" * 60)
        print(f"检查完成！")
        print(f"可用卡密: {len(available_cards)} 个")
        print(f"不可用卡密: {len(unavailable_cards)} 个")

        # 保存可用卡密
        if available_cards:
            with open('available_cards.txt', 'w', encoding='utf-8') as f:
                for card in available_cards:
                    f.write(f"{card}\n")
            print(f"可用卡密已保存到 available_cards.txt")

        # 保存不可用卡密详情
        if unavailable_cards:
            with open('unavailable_cards.txt', 'w', encoding='utf-8') as f:
                for item in unavailable_cards:
                    f.write(f"{item['card']} - {item['error']}\n")
            print(f"不可用卡密详情已保存到 unavailable_cards.txt")

    except FileNotFoundError:
        print("错误: card.txt 文件未找到")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    check_all_cards()