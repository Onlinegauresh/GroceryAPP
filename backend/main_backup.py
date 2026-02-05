from preview_router import router as preview_router
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(inventory_router)
app.include_router(accounting_router)
== == == =
# Configure static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers from microservices
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(inventory_router)
app.include_router(accounting_router)

# Include preview router
app.include_router(preview_router)
