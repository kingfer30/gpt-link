import requests
import time
import json

def check_card_key(card):
    """检查单个卡密的可用性"""
    url = f"https://ow521.com/api/card-keys/{card}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        return {"available": False, "error": f"网络请求错误: {str(e)}"}
    except json.JSONDecodeError:
        return {"available": False, "error": "响应格式错误"}

def check_cards_sample():
    """检查前5个卡密作为测试"""
    try:
        # 读取卡密文件前5行
        with open('card.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()[:5]

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

        print(f"测试检查前 {len(cards)} 个卡密...")
        print("-" * 50)

        for i, card in enumerate(cards, 1):
            print(f"[{i}/{len(cards)}] 检查卡密: {card}")

            result = check_card_key(card)

            if result.get("available", False):
                print(f"  [OK] 可用")
            else:
                error_msg = result.get("error", "未知错误")
                print(f"  [FAIL] 不可用 - {error_msg}")

            time.sleep(0.1)

        print("-" * 50)
        print("测试完成！")

    except FileNotFoundError:
        print("错误: card.txt 文件未找到")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    check_cards_sample()