import requests

url = "https://microsoft-translator-text.p.rapidapi.com/translate"

querystring = {"to[0]":"ml","api-version":"3.0","profanityAction":"NoAction","textType":"plain"}

payload = [{ "Text": "I would really like to drive your car around the block a few times." }]
headers = {
	"content-type": "application/json",
	"X-RapidAPI-Key": "bbe34dfedcmshec917ab859bf61ap1c9df1jsn1de7568a3cc1",
	"X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
}

response = requests.post(url, json=payload, headers=headers, params=querystring)

print(response.json())