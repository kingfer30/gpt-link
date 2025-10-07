import requests
import json
import webbrowser
import subprocess
import sys
import argparse

def fetch_checkout(access_token):
    """
    模拟JavaScript的fetch调用:
    1. 使用传入的accessToken调用checkout API
    2. 获取返回的URL并用Chrome打开
    """
    
    try:
        if not access_token:
            print("错误: 请提供access_token")
            return
            
        print(f"使用accessToken: {access_token[:20]}...")
        
        # 调用checkout API
        print("正在调用checkout API...")
        headers = {
            "accept": "*/*",
            "accept-language": "en",
            "authorization": f"Bearer {access_token}",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "cookie": "__Host-next-auth.csrf-token=622c50c8db3224e191223ed8cdc669e9f655b6bdc9e6bbea856ee52e672a300c%7C0e4cb5fdf3c4e0e34afb2338f06995082749121318f269387f94b4104532402c; oai-did=ed18a99c-f5f8-4626-9f84-658f0f7b30ab; __cf_bm=0zIDj9sT65w5EHMSxTK7X0grHWBpyc90U_k7bHnfrLA-1758901746-1.0.1.1-G_rZ3i7aomiVVfFkVOWHLnaptrBID7KMXYoTWUt_T9l2MX_C0bugvlTH_BqClylXRTokv7oBgyqLQgHzx6Hs0vP9V4dGWm9B4fBIfBM.xB0; __cflb=0H28vzvP5FJafnkHxisysZqwgQPnhNv6iBWAxp55e7D; _cfuvid=5XOinjc.ZiLT3Ynnpf8iSxWWqLXKl3n_mnIKm0fDHxs-1758901746794-0.0.1.1-604800000; cf_clearance=sJX59R5QTcjLXqbSUy4bq5J0rZvxJJNJxoJ3lTdsLTU-1758901749-1.2.1.1-TwTH.w7dALc1JpASfWyr58Y3awNTeTGPsVrm6JXrUwn0PN6ni0kcwdir1V14OwppT8MgQ4j7BWZjZiakBP6xNLWIJj.A6kdAn34dQXh.9B4OXZRd7zcU4BP2N9IT76twBSNzzWLMTD7pVvoabm4txsYAUjrJ4M3Ru1spyCt3voqS5LoWRgfv6ep2nLsyuqAfPx9FpX01Ov1oxxD_pvXc.HZPeIrh_TUTaCEt_TGhOnM; __Secure-next-auth.callback-url=https%3A%2F%2Fchatgpt.com%2F; oai-hlib=true; oai-sc=0gAAAAABo1rYrtTp52-YWtoa9uu6ndtDPd7XRJOzL_lRgg4P2gwadzSnn6w6kH3c0aPBez0YNVbYwvDit_m3gPV4Mi0hs8INCihBBg59d7LI6-DMyNCeq-2xR-xJznHYXPOAeYzO23AbCvsd_dbeGuLbxfrAS_bcM0pl7OlPMKDpLa47C9lHwAQh_lOypPtkfmJycbobRGSn_SjIty55-AW70urQSXXax7zqDwbebGXN7lAcQFsem11g; oai-model-sticky-for-new-chats=false; oai-gn=; oai-hm=WHAT_ARE_YOU_WORKING_ON%20%7C%20GOOD_TO_SEE_YOU; _dd_s=aid=8349c0e6-6e9b-4dc0-a7e7-d1c35773c8e3&rum=0&expire=1758902838122&logs=1&id=db4c1372-542a-4540-beeb-5dbe7c9f65f6&created=1758901749068; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..QLzwpZnNRniB8458.VwfjtP-5vIM_ECTTI6eRrNtOAt3HnorR2sqomvFe8bECTM8GY4fDFwghm7lT6uHgEcWmxoonjWIzfJjLryKCyWWcV7kcR-l2F6RtJ9VrVa31XHO_-c6Y-rq6OpPZIo9LYFnNG9Kxx8ef89S2lnBCgX_mPSGO1aB_p0Trs100_FFFl-EQ4LSr11T_pVjIsZ5PT1WeQ2Y1zGB2BbuFwdLLWs3x9WZwB7lpENdx17FifTCur1-PbwpIJSpC7DZ6PRxr0WWjKZvBCf2ZPBbZgmx_1pETVfh9TTCzmF2ECX-Fqmod8nbNKhJlWWRjo6-DD6dURb8GzguOyZC14tjEh7YJEkeuKyVSaORU-P-qlCjr7Ily_7hjDypyTBDCWdZn_HL55YFjjrXO5aQVZ6u7unWfZe4o8uc42OKVhM5aY0rfrmdFCQdAltmhRhwS_gOtfiCJbncvocwz4g0LSXwxOS25rhvccVPhCkCIt1ZCETsh9-1-l--mZQIonijWthCgVgIU_oBZqQqhScPcMuPjiWhfQaXi8b4xTowuBK22smxx2DumCNiQPglA3St8FJbIJJJ2_ophjW9g6DQRBLFEcza1QkqcKq5tbAxO9Dk-Zx7TVrVtz6DwRHReUiZKnhOlRyXq9WHfdjHyyp4B8WHvTn8AxGvYx1Q0jEOT07WQ4qMvBsHXtlgRIlgTG1iMEDhOIaWrB9OOuHlVBvFlJ7MEBjkGKueRCo8iSPUwAMUuo0mIeZvJbqOu8Qon4-GZ7J6etmxJMX5cFBmSYoHrWgz1VAYWlG-_gUmJei0_4D_DNRT0VLikRM9wTplCuigck9Z7M6LCouMXGFKB6NdriMXCdobPxoLeSXbuQt0tFFenwjhqFl5K5fepsCM1_hwYqJh-PhI-RADogkldVAHohnxwHPNaCkW8FWyPn2UGleMiAmnOf0k5W-S3F7HhXAjSfYCBbXxUkbhFkUYVA4GgG7tR_98Q4Y9-k9ZpxxghcrReEJJ8sbfJHaofg7GlFyeDErUoV4rE57xfhvKlsm5Bt0Vn7VRH4x99Kgma_ndSfaIELtoUnEon5rQ4oEAkCSqdyLtsbzNx7gwOdaZOkYIc7mBXBMFuJHwf1tLjg1wpSFuZJR5ZAyNIH2-xr1tcVMjJBT-h6_UjC5XeoKR0i4E5LTbSrv6mT0EsJLBXLvOjt6dpTqkyegF4PfWTKHQsSafAQJ6q7ZQGSEbCwfuZ5QSB9LkPWC3uPL4SJLzQLRXEPlP-nXTuGSCnvT7JwEE0Ex1xcvOh7eCMK5svc53J8Ia97xBE0-a4dSKM-tI5Qtt4SQEmUfhCzZNB1uTQdMkuRwscyJ851dcKzlBvBj7rspQdSUsVBmN_VGunTzfM5169DL0i3YSA--uSDRIk_Rjr6od7zhjqjH2xD0f2UBBbgCcN_LyiC8V2cUFvRvrlQIZtFUI1w4ynwTsOJecs3ESyXNieD36g4HIZQ2aNVbiLzIl27EisgmmQggvuxqAOuP0K841xppXQUvTT4DOix2fKGXnMp9SvGdfSOOtrhVfh889xU25D9nf-aQTSI9PU7hnKgAAfubh0ywNYjI6szmlzDg_ngTEqVp_dazH_nex2Evh169B4mpAMQOtuAZ5VAcAP-opGMxZnlBkG_TyxQJZ8hM225shpw6Kd8Bsccbx0paTGnzi2p5xPDmLONA3nl_35aHChNCzFAimTby1w57Se8--NotM2F7Oco2jWpknW337L88lRvnfai7z-TzJ-cHRva2f3RF3MDuZIR1ISvDmnZfaCR-5JlRwXcpq8VWMEy7cWoK4nENO9U6iHf7LCvRWkr545KMwSfzrWpTDZE0y4oPUPSmWt5MD6V7WvbZkB36pFqQeXh6F1qKm0A1nTbfF91STN0y58aoGoEaFfuKUfxFzFEF-FnNTJCM-uNIvJJwebOFhplgiWepibX0hqDECfSuTTa4CIm-f4hyvgHhXqNNnrN5rFqs3Mp_rtto3-z07BpqpMrQRYZ1UAQBIo7SXLoLmtEc7tc9eWz9WYw7RkwQHIRrhO727Aw6c-BD7sUgCBtMaWtLnTGUmV39siOk9sEAT7mfGAKMpnivrlbjFDQWeFCEfF8AfSk9EahtGia0pjfHGB1k0FHQxBx1OYLMOsiei5GFJQxKnc1n1VRZ3zA5LBJOQ2ZXa2gXyKBCukA1bPwH4-QvzkeZxvBqoyou5AXek0LKOqYsKe1kPr1oTje5tJ1bXJO6mFgfyfRyGqDrhHx7VzAve6BRFdNsKVemC7lw7f3MqTQSlCVZWuIX6L1S-FVReX2LPR3kQoCPBRWGzbR1rAtE3cSv75zZSTbGz-HtDWJGTCMADGrY66kfwvO38I9gTA3Ws15tJ4HsSEpjpRaYTeoLfinko97t56xACIgd4Bc7Gey0TUmh9rG678L-oSth3IR5FrXZeVDb-rwQgMj3TvhMRQn8Ed8ONHut8xY8TzydaqWxh0Gxsf5csfKfE72EVO3D_lM27gqRVpl8aQuqueMZP7GC99W7M1ogZb7iu_Gq0TxW9ChenIN0tW48VCWSHAoI0LyiePVS2dlBP3cWNojHY6V75rDGOKgsZZlRDZRe3c21opb8l4WcXDeYM6VqiCvYazbkyw4a_0aMki-x5ELhC8rRTNRr2ea35lWiDegfnBoZ_8SW_8EyfOan5PCKya6f5tTUMuNbWI1qdXFljF-fFmNWAgw0DzrOZn7I-w_34q4ZKIvcrGLafVM0Od4mmwFYK5w1AiUym-wM5Ne1KxJbqbCJsS6EQpSNTXN2Cqpcq8lBymMh8Ib0uVJWmwt7S8ciZibvlxu4TO26ePSKnaucex-tMukpcIhKWw5gwkEO2sxuJ2abPqslpXx5gJalcs5zIU11J3bRXVL7pHpkuTfgXFFAorc_SA0kRi1Rk9aSf80SVdWE50eYY7vXL-DjDeOYz65CnMMjFBSiTbaLB8F9O8IiaC45as21WGVRR0Kr9ggzyH.kHCLk8VittDiKKdNgQUkRw",
            "Referer": "https://chatgpt.com/",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        
        checkout_response = requests.post("https://chatgpt.com/backend-api/payments/checkout", 
                                        headers=headers,
                                        json={})
        print
        if checkout_response.status_code != 200:
            print(f"Checkout API调用失败: {checkout_response.status_code}")
            return
            
        checkout_data = checkout_response.json()
        checkout_url = checkout_data.get('url')
        
        if not checkout_url:
            print("未找到checkout URL")
            return
            
        print(f"成功获取checkout URL: {checkout_url}")
        
        # 第三步: 使用Chrome打开URL
        open_url_in_chrome(checkout_url)
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

def open_url_in_chrome(url):
    """
    自动打开Chrome浏览器并访问指定URL
    """
    try:
        print(f"正在用Chrome打开: {url}")
        
        # Windows下的Chrome路径
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
        ]
        
        chrome_found = False
        for chrome_path in chrome_paths:
            try:
                subprocess.run([chrome_path, url], check=True)
                chrome_found = True
                print("成功打开Chrome浏览器")
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if not chrome_found:
            # 如果找不到Chrome，使用默认浏览器
            print("未找到Chrome，使用默认浏览器打开")
            webbrowser.open(url)
            
    except Exception as e:
        print(f"打开浏览器失败: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='模拟fetch checkout API调用并打开浏览器')
    parser.add_argument('--access_token', required=True, help='Bearer token用于API认证')
    
    args = parser.parse_args()
    fetch_checkout(args.access_token)