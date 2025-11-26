

#apikey = "AIzaSyAEqLj9nXtf89c4NsYjQacXOL45toosYIE"
#task_name = input("Feladatsor neve: ")
#task_topic = input("Feladatsor témája")
#num_of_task = int(input("Feladatok száma: "))
def gen_task(api_key, task_name, task_topic, num_of_task):
    from google import genai

    client = genai.Client(api_key=api_key)




    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="""Csinálj json formátumban egy feladatsort ilyen formában:
        [
            {
                "question": "Oldd meg az egyenletet: 0.5x + 2 = 3x - 1",
                "type": "text",
                "answer": ["1.2"],
                "points": 1,
                "match_type": "number"
            }
        ]
        , a témakör legyen: """+ task_topic+f", és a témakörből {num_of_task} mennyiségü kérdést generálj. Csak a json végeredményt mondjad. Használható 'match_type'-ok: contains, number, exact",
    )
    print(response.text)
    with open(f"quizzes/{task_name}.json", "w") as f:
        f.write(response.text[7:-3])
#gen_task(api_key=apikey, task_name=task_name, task_topic=task_topic, num_of_task=num_of_task)