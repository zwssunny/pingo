from gradio_client import Client

client = Client("http://localhost:8080/")
# result = client.predict(
# 		vocie_selection="Default",
# 		api_name="/on_voice_change"
# )
# print(result)

# result = client.predict(
# 		api_name="/generate_seed"
# )
# print(result)
# result = client.predict(
# 		api_name="/generate_seed_1"
# )
# print(result)
# result = client.predict(
# 		coef="嵃繳谊瀛巵蛁勾菫噏貍箄跚偄燵兕訿薽孓袁庁嶡跆廼仁瑎蝍埔贀螠膭塄瀿猤廣誠簞嶡点拹貨柏訩第贯舘燺帱儿攝潳蠫坕巰巐曵稟趏瀅佘豂琿燤焁樿紮藣螡觟嶵孍囸刈亏激筴豧嫚臿岼房刨尳袐啀嶀剪曰渗堏簴潘跾浀函堚紾爂嬣萚詆巙潸苻丩挏帏綠谥埅臾緬贿赌刓諜佘巭偻固樂序笪朠贱挋凵槠栿琞埃蕳媅嶨俐苿劫晏盯蒼賀洘臜羓倾僋萳跚昍巂肀滿獺俏莍蚌赻枛凸暪戾蜐蘣褱箢嶻湂滽櫵罏祁侀谨疚函校萿攻哓識浨巒幅滿苰悏湳埰趌赡燨凁圼囆戓販喰嶨専諾读婏蟌樘趺腛臿羄蔾澨娣蚃燄嶮七相乗丏豽佤趂竦凬崸洿谸拃螸盦嶀㴁",
# 		api_name="/reload_chat"
# )
# print(result)
# result = client.predict(
# 		api_name="/lambda"
# )
# print(result)
result = client.predict(
		text="四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",
		text_seed_input=42,
		refine_text_flag=True,
		api_name="/refine_text"
)
print(result)
# result2 = client.predict(
# 		text=result,
# 		temperature=0.3,
# 		top_P=0.7,
#         top_K=20,
#         audio_seed_input=2,
#         stream=False,
# 		api_name="/generate_audio"
# )
# print(result2)