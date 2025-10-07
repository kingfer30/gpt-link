import requests

proxyip = "http://storm-aiguoguo_area-US:a1chat199@us.stormip.cn:1000"
url = "http://api.ip.cc"
proxies={
    'http':proxyip,
    'https':proxyip,
}
data = requests.get(url=url,proxies=proxies)
print(data.tvvvvvvvext)