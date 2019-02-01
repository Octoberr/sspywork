import  requests

url = 'https://www.google.com/search?newwindow=1&hl=en&ei=IuuEW8zcLYaf0gL-maVo&q=twitch+android+app+download&oq=twitch+andr+app+download&gs_l=psy-ab.3.0.0i7i30k1j0i8i7i30k1l3.18520.22367.0.24246.5.5.0.0.0.0.288.1084.2-4.4.0....0...1c.1.64.psy-ab..1.3.819...35i39k1j0i13k1.0.HMLsBC4Ra_4'
res = requests.get(url)
print(res.text)