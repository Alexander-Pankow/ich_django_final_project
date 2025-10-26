from django.http import HttpResponse

def home(request):
    html_content = """
    <html>
        <head>
            <title>Ich Django Final Project</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin-top: 100px;
                    background-color: #f5f5f5;
                }
                h1 {
                    color: #333;
                }
                .button {
                    display: inline-block;
                    margin: 20px 10px 0 10px;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }
                .button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <h1>Ich Django Final Project</h1>
            <a href="/api/docs/" class="button">Swagger UI</a>
            <a href="/admin/" class="button">Admin panel</a>
        </body>
    </html>
    """
    return HttpResponse(html_content)