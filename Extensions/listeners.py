from twitchio.ext import pubsub

async def listen_to_pubsub(bot, access_token, broadcaster_id):

    topics = [
        pubsub.channel_points(token=access_token)[int(broadcaster_id)],
        pubsub.bits(token=access_token)[int(broadcaster_id)],
        pubsub.channel_subscriptions(token=access_token)[int(broadcaster_id)],
    ]
    await bot.pubsub.subscribe_topics(topics)
