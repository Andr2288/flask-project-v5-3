import asyncio
import aiohttp
from aiohttp import web, ClientSession
import json
import aiofiles
from datetime import datetime
import os


async def get_external_data():
    """Get data from external API asynchronously"""
    async with ClientSession() as session:
        try:
            # Example: get weather data
            async with session.get('https://api.openweathermap.org/data/2.5/weather?q=Kyiv&appid=demo') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {'status': 'success', 'data': data}
                else:
                    return {'status': 'error', 'message': 'Failed to get weather data'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


async def process_data_async(data):
    """Process data asynchronously"""
    await asyncio.sleep(0.1)  # Simulate processing time
    processed = {
        'original_data': data,
        'processed_at': datetime.utcnow().isoformat(),
        'word_count': len(str(data).split()),
        'character_count': len(str(data))
    }
    return processed


async def log_activity_async(activity):
    """Log activity to file asynchronously"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'activity': activity
    }

    try:
        async with aiofiles.open('async_logs.txt', 'a') as f:
            await f.write(json.dumps(log_entry) + '\n')
        return True
    except Exception as e:
        print(f"Logging error: {e}")
        return False


async def handle_async_posts(request):
    """Handle async posts endpoint"""
    try:
        await log_activity_async('Async posts endpoint accessed')

        # Simulate database query
        await asyncio.sleep(0.05)

        posts_data = [
            {
                'id': 1,
                'title': 'Async Flask Blog',
                'content': 'This is processed asynchronously',
                'author': 'async_user',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'title': 'Aiohttp Integration',
                'content': 'Combining Flask with aiohttp for better performance',
                'author': 'async_user',
                'created_at': datetime.utcnow().isoformat()
            }
        ]

        # Process data asynchronously
        processed_posts = []
        for post in posts_data:
            processed = await process_data_async(post)
            processed_posts.append(processed)

        return web.json_response({
            'status': 'success',
            'posts': processed_posts,
            'total': len(processed_posts)
        })

    except Exception as e:
        await log_activity_async(f'Error in async posts: {str(e)}')
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)


async def handle_external_data(request):
    """Handle external data fetching"""
    try:
        await log_activity_async('External data fetch requested')

        # Get data from external source
        result = await get_external_data()

        if result['status'] == 'success':
            # Process the external data
            processed = await process_data_async(result['data'])

            return web.json_response({
                'status': 'success',
                'external_data': result['data'],
                'processed_data': processed
            })
        else:
            return web.json_response(result, status=400)

    except Exception as e:
        await log_activity_async(f'Error fetching external data: {str(e)}')
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)


async def handle_batch_processing(request):
    """Handle batch processing of multiple requests"""
    try:
        data = await request.json()
        items = data.get('items', [])

        await log_activity_async(f'Batch processing {len(items)} items')

        # Process all items concurrently
        tasks = [process_data_async(item) for item in items]
        results = await asyncio.gather(*tasks)

        return web.json_response({
            'status': 'success',
            'processed_items': results,
            'total_processed': len(results)
        })

    except Exception as e:
        await log_activity_async(f'Error in batch processing: {str(e)}')
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)


async def handle_async_analytics(request):
    """Handle analytics data processing"""
    try:
        await log_activity_async('Analytics request received')

        # Simulate multiple async operations
        tasks = [
            get_external_data(),
            process_data_async({'type': 'user_activity'}),
            process_data_async({'type': 'post_statistics'}),
            process_data_async({'type': 'comment_analysis'})
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        analytics_data = {
            'external_weather': results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])},
            'user_activity': results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])},
            'post_stats': results[2] if not isinstance(results[2], Exception) else {'error': str(results[2])},
            'comment_analysis': results[3] if not isinstance(results[3], Exception) else {'error': str(results[3])},
            'generated_at': datetime.utcnow().isoformat()
        }

        return web.json_response({
            'status': 'success',
            'analytics': analytics_data
        })

    except Exception as e:
        await log_activity_async(f'Error in analytics: {str(e)}')
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)


async def handle_websocket_echo(request):
    """Handle WebSocket connections for real-time communication"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    await log_activity_async('WebSocket connection established')

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)

                # Process message asynchronously
                processed = await process_data_async(data)

                response = {
                    'type': 'echo',
                    'original': data,
                    'processed': processed,
                    'timestamp': datetime.utcnow().isoformat()
                }

                await ws.send_str(json.dumps(response))
                await log_activity_async(f'WebSocket message processed: {data}')

            except json.JSONDecodeError:
                await ws.send_str(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print(f'WebSocket error: {ws.exception()}')

    await log_activity_async('WebSocket connection closed')
    return ws


async def handle_health_check(request):
    """Health check endpoint"""
    await log_activity_async('Health check requested')

    return web.json_response({
        'status': 'healthy',
        'service': 'async_service',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


def create_async_app():
    """Create aiohttp application"""
    app = web.Application()

    # Add routes
    app.router.add_get('/async/posts', handle_async_posts)
    app.router.add_get('/async/external', handle_external_data)
    app.router.add_post('/async/batch', handle_batch_processing)
    app.router.add_get('/async/analytics', handle_async_analytics)
    app.router.add_get('/async/ws', handle_websocket_echo)
    app.router.add_get('/async/health', handle_health_check)

    return app


async def run_async_server():
    """Run the async server"""
    app = create_async_app()

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    print("Async server started on http://localhost:8080")
    print("Available endpoints:")
    print("  GET  /async/posts - Get posts asynchronously")
    print("  GET  /async/external - Fetch external data")
    print("  POST /async/batch - Batch processing")
    print("  GET  /async/analytics - Analytics data")
    print("  GET  /async/ws - WebSocket echo")
    print("  GET  /async/health - Health check")

    await log_activity_async('Async server started')


if __name__ == '__main__':
    asyncio.run(run_async_server())