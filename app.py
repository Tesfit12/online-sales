from my_market import app, models, routes, db


@app.shell_context_processor
def shell_context():
    return {
        'models': models,
        'app': app,
        'db': db,
        'routes': routes
    }


if __name__ == '__main__':
    v = input("Do you want to populate database?[y/n]")
    if v == 'y':
        from my_market import populate
    app.run(debug=True)

