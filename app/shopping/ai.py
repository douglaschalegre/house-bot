import asyncio

from openai import OpenAI


async def sort_items(client: OpenAI, items: list[str]) -> str:
    item_text = "\n".join(items)
    prompt = f"""Por favor, organize esta lista de compras de forma lógica,
agrupando itens similares.
Considere categorias como hortifruti, laticínios, carnes, produtos de despensa, etc.
Para cada item, adicione um marcador (-) e mantenha os nomes originais dos itens.
Aqui está a lista:
{item_text}"""

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that organizes shopping lists "
                    "into logical categories."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The shopping list sorter returned an empty response")
    return content.strip()

