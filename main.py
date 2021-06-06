import discord
import logging
import requests
import json
from discord.ext import commands
import numpy as np

#logs info
logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix='$fmna ')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# @bot.event
# async def on_message(message):
#     print('test')
#     if message.author == bot.user:
#         return

#     if message.content.startswith('$test'):
#         await message.channel.send('test')
        
@bot.command()
async def recommend(ctx, anilist_name: str):
    print('start')
    url = "https://graphql.anilist.co"

    #get tags
    tag_query = '''
    query{
        MediaTagCollection{
            name
        }
    }
    '''
    tag_response = requests.post(url, json={'query': tag_query}).json()

    tag_list = []
    for dic in tag_response['data']['MediaTagCollection']:
        tag_list.append(dic['name'])

    tag_map = {k: v for v, k in enumerate(tag_list)}

    user_query = '''
    query($userName: String){
        MediaListCollection(userName: $userName, type: ANIME, status_in: [COMPLETED]){
            lists{
                entries{
                    score
                    media{
                        title{
                            romaji
                        }
                        tags{
                            name
                            rank
                        }
                    }
                }
            }
        }
    }
    '''

    unseen_query = '''
    query($page: Int){
        Page(perPage: 50 page: $page){
                pageInfo{
                    lastPage
                }
            media(onList: false, type: ANIME, isAdult: false, format_in: [TV, MOVIE, ONA], status_in: [FINISHED, RELEASING], 
            startDate_greater: 19800101, popularity_greater: 10000, averageScore_greater: 60){
                siteUrl
                tags{
                    name
                    rank
                }
            }
        }
    }
    '''

    user_variables = {
        'userName': anilist_name
    }

    user_response = requests.post(url, json={'query': user_query, 'variables': user_variables}).json()
    anime_list = user_response['data']['MediaListCollection']['lists'][0]['entries']

    weights = [0] * len(tag_list)
    for anime in anime_list:
        for tag in anime['media']['tags']:
            weights[tag_map[tag['name']]] += anime['score'] * tag['rank']

    unseen_list = []
    for i in range(1, 30):
        unseen_variables = {
            'page': i
        }
        unseen_response = requests.post(url, json = {'query': unseen_query, 'variables': unseen_variables}).json()
        unseen_list += unseen_response['data']['Page']['media']

    scores = []
    for anime in unseen_list:
        score = 0
        for tag in anime['tags']:
            score += weights[tag_map[tag['name']]] * tag['rank']
        scores.append(score * -1)

    rankings = np.argsort(scores)
    rankings = rankings[:50]
    recommendation_list = []

    for index in rankings:
        anime_info = {}
        # anime_info['id'] = unseen_list[index]['id']
        # anime_info['img_URL'] = unseen_list[index]['coverImage']['medium']
        # anime_info['romaji'] = unseen_list[index]['title']['romaji']
        anime_info['site_URL'] = unseen_list[index]['siteUrl']
        recommendation_list.append(anime_info)
    print(recommendation_list[0]['site_URL'])
    await ctx.send(recommendation_list[0]['site_URL'])



bot.run('NzY5NzUzODAzMDE5OTExMTkw.X5TnFw.VUEjFmIZ43RSWxZU_ASQ6H3kdx8')
