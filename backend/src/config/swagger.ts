import swaggerJsdoc from "swagger-jsdoc";

const swaggerDefinition = {
  openapi: "3.0.0",
  info: {
    title: "E-Commerce Intelligent Platform API",
    version: "1.0.0",
    description:
      "Backend API for the E-Commerce Intelligent Platform. Provides product catalog, orders, reviews, user management, ML predictions, and voice confirmation services.",
  },
  servers: [
    {
      url: "http://localhost:5000",
      description: "Development server",
    },
  ],
  tags: [
    { name: "Health", description: "Server health check" },
    { name: "Auth", description: "Authentication endpoints (register, login, logout)" },
    { name: "Users", description: "User profile and admin management" },
    { name: "Products", description: "Product catalog CRUD" },
    { name: "Categories", description: "Product categories" },
    { name: "Subcategories", description: "Product subcategories" },
    { name: "Orders", description: "Order management" },
    { name: "Reviews", description: "Product reviews" },
    { name: "ML", description: "Machine learning operations and price prediction" },
    { name: "Voice", description: "Phone order confirmation (Retell AI)" },
    { name: "Chat", description: "Customer support chat (AI-powered)" },
  ],
  components: {
    securitySchemes: {
      cookieAuth: {
        type: "apiKey",
        in: "cookie",
        name: "access_token",
        description: "JWT token stored in httpOnly cookie",
      },
    },
    schemas: {
      ApiResponse: {
        type: "object",
        properties: {
          success: { type: "boolean" },
          message: { type: "string" },
          data: { type: "object", nullable: true },
          errors: { type: "object", nullable: true },
        },
      },
      User: {
        type: "object",
        properties: {
          id: { type: "integer" },
          email: { type: "string", format: "email" },
          role: { type: "string", enum: ["customer", "admin", "manager"] },
          first_name: { type: "string" },
          last_name: { type: "string" },
          phone: { type: "string", nullable: true },
          is_active: { type: "boolean" },
          created_at: { type: "string", format: "date-time" },
        },
      },
      RegisterInput: {
        type: "object",
        required: ["first_name", "last_name", "email", "password"],
        properties: {
          first_name: { type: "string", example: "John" },
          last_name: { type: "string", example: "Doe" },
          email: { type: "string", format: "email", example: "john@example.com" },
          password: { type: "string", minLength: 8, example: "password123" },
        },
      },
      LoginInput: {
        type: "object",
        required: ["email", "password"],
        properties: {
          email: { type: "string", format: "email", example: "john@example.com" },
          password: { type: "string", example: "password123" },
        },
      },
      Product: {
        type: "object",
        properties: {
          id: { type: "integer" },
          title: { type: "string" },
          description: { type: "string" },
          brand: { type: "string" },
          price: { type: "number" },
          discount_percent: { type: "number" },
          stock: { type: "integer" },
          category_id: { type: "integer" },
          subcategory_id: { type: "integer" },
          tags: { type: "array", items: { type: "string" } },
          images: { type: "array", items: { type: "string" } },
          thumbnail: { type: "string" },
          is_active: { type: "boolean" },
          rating_avg: { type: "number" },
          review_count: { type: "integer" },
          created_at: { type: "string", format: "date-time" },
        },
      },
      ProductInput: {
        type: "object",
        required: ["title", "description", "brand", "price", "stock", "category_id"],
        properties: {
          title: { type: "string", example: "Wireless Headphones" },
          description: { type: "string", example: "High-quality Bluetooth headphones" },
          brand: { type: "string", example: "Acme" },
          price: { type: "number", example: 99.99 },
          discount_percent: { type: "number", example: 10 },
          stock: { type: "integer", example: 50 },
          category_id: { type: "integer", example: 1 },
          subcategory_id: { type: "integer", example: 2 },
          tags: { type: "string", example: '["audio","wireless"]', description: "JSON string when sent as multipart" },
          is_active: { type: "string", example: "true", description: "String bool when sent as multipart" },
        },
      },
      Category: {
        type: "object",
        properties: {
          id: { type: "integer" },
          name: { type: "string" },
          description: { type: "string" },
          created_at: { type: "string", format: "date-time" },
        },
      },
      CategoryInput: {
        type: "object",
        required: ["name"],
        properties: {
          name: { type: "string", example: "Electronics" },
          description: { type: "string", example: "Electronic devices and accessories" },
        },
      },
      Subcategory: {
        type: "object",
        properties: {
          id: { type: "integer" },
          name: { type: "string" },
          category_id: { type: "integer" },
          created_at: { type: "string", format: "date-time" },
        },
      },
      SubcategoryInput: {
        type: "object",
        required: ["name", "category_id"],
        properties: {
          name: { type: "string", example: "Headphones" },
          category_id: { type: "integer", example: 1 },
        },
      },
      Order: {
        type: "object",
        properties: {
          id: { type: "integer" },
          user_id: { type: "integer" },
          status: { type: "string", enum: ["pending", "processing", "shipped", "delivered", "cancelled", "on_hold", "pending_phone_confirmation", "manual_review"] },
          total_amount: { type: "string" },
          payment_status: { type: "string" },
          items: { type: "array", items: { $ref: "#/components/schemas/OrderItem" } },
          created_at: { type: "string", format: "date-time" },
        },
      },
      OrderItem: {
        type: "object",
        properties: {
          product_id: { type: "integer" },
          quantity: { type: "integer" },
          unit_price: { type: "string" },
          product_name_snapshot: { type: "string" },
        },
      },
      CreateOrderInput: {
        type: "object",
        required: ["items", "payment_method"],
        properties: {
          items: {
            type: "array",
            items: {
              type: "object",
              properties: {
                product_id: { type: "integer", example: 1 },
                quantity: { type: "integer", example: 2 },
              },
            },
          },
          payment_method: { type: "string", enum: ["credit_card", "cash_on_delivery", "apple_pay"], example: "credit_card" },
        },
      },
      Review: {
        type: "object",
        properties: {
          id: { type: "integer" },
          product_id: { type: "integer" },
          user_id: { type: "integer" },
          rating: { type: "integer", minimum: 1, maximum: 5 },
          review_text: { type: "string" },
          created_at: { type: "string", format: "date-time" },
        },
      },
      ReviewInput: {
        type: "object",
        required: ["product_id", "rating"],
        properties: {
          product_id: { type: "integer", example: 1 },
          rating: { type: "integer", example: 5, minimum: 1, maximum: 5 },
          review_text: { type: "string", example: "Great product!" },
        },
      },
      MLSegment: {
        type: "object",
        required: ["user_id", "segment_id", "segment_label", "model_name", "model_version"],
        properties: {
          user_id: { type: "integer", example: 1 },
          segment_id: { type: "integer", example: 2 },
          segment_label: { type: "string", example: "High Value" },
          model_name: { type: "string", example: "kmeans" },
          model_version: { type: "string", example: "v1.0" },
          confidence: { type: "number", example: 0.95 },
        },
      },
      MLModelRegistration: {
        type: "object",
        required: ["model_name", "model_version", "model_type", "algorithm"],
        properties: {
          model_name: { type: "string", example: "kmeans_customer" },
          model_version: { type: "string", example: "1.0.0" },
          model_type: { type: "string", example: "segmentation" },
          algorithm: { type: "string", example: "kmeans" },
          metrics: { type: "object", example: { silhouette_score: 0.65 } },
          parameters: { type: "object", example: { n_clusters: 5 } },
          artifact_path: { type: "string", example: "s3://models/kmeans_v1.pkl" },
        },
      },
      PricePredictionInput: {
        type: "object",
        properties: {
          product_id: { type: "integer", example: 10 },
          title: { type: "string", example: "Wireless Headphones" },
          brand: { type: "string", example: "Acme" },
          category_id: { type: "integer", example: 1 },
          subcategory_id: { type: "integer", example: 2 },
          stock: { type: "integer", example: 50 },
          tags: { type: "array", items: { type: "string" }, example: ["audio", "wireless"] },
        },
      },
      VoiceInitiateResponse: {
        type: "object",
        properties: {
          orderId: { type: "integer" },
          providerCallId: { type: "string" },
        },
      },
      VoiceContext: {
        type: "object",
        properties: {
          id: { type: "integer" },
          order_id: { type: "integer" },
          phone_number: { type: "string" },
          call_status: { type: "string" },
          provider_call_id: { type: "string" },
          transcript: { type: "string", nullable: true },
          confirmed: { type: "boolean", nullable: true },
          retry_count: { type: "integer" },
          created_at: { type: "string", format: "date-time" },
        },
      },
      ChatInput: {
        type: "object",
        required: ["query"],
        properties: {
          query: { type: "string", example: "Show me wireless headphones under $100", maxLength: 500 },
          session_id: { type: "string", example: "abc-123" },
        },
      },
      ChatResponse: {
        type: "object",
        properties: {
          query: { type: "string" },
          response: { type: "string" },
          context_used: { type: "array", items: { type: "object" } },
          algorithm: { type: "string" },
          session_id: { type: "string" },
        },
      },
      Error: {
        type: "object",
        properties: {
          success: { type: "boolean", example: false },
          message: { type: "string" },
          errors: { type: "object", nullable: true },
        },
      },
    },
  },
  paths: {
    "/api/health": {
      get: {
        tags: ["Health"],
        summary: "Server health check",
        responses: {
          200: {
            description: "Server is healthy",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "string", example: "success" },
                    message: { type: "string", example: "Server is healthy" },
                    timestamp: { type: "string", format: "date-time" },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/api/auth/register": {
      post: {
        tags: ["Auth"],
        summary: "Register a new user",
        security: [],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/RegisterInput" } } },
        },
        responses: {
          201: {
            description: "Registration successful",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } },
            headers: {
              "Set-Cookie": { schema: { type: "string", description: "access_token cookie" } },
            },
          },
          400: { description: "Validation error", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
          429: { description: "Too many requests (rate limited)" },
        },
      },
    },
    "/api/auth/register-admin": {
      post: {
        tags: ["Auth"],
        summary: "Register a new admin user (admin only)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/RegisterInput" } } },
        },
        responses: {
          201: {
            description: "Admin registration successful",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } },
          },
          400: { description: "Validation error", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } },
          },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
          409: { description: "Email already registered" },
        },
      },
    },
    "/api/auth/login": {
      post: {
        tags: ["Auth"],
        summary: "Login with email and password",
        security: [],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/LoginInput" } } },
        },
        responses: {
          200: {
            description: "Login successful",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } },
            headers: {
              "Set-Cookie": { schema: { type: "string", description: "access_token cookie" } },
            },
          },
          401: { description: "Invalid credentials" },
          429: { description: "Too many requests (rate limited)" },
        },
      },
    },
    "/api/auth/logout": {
      post: {
        tags: ["Auth"],
        summary: "Logout and revoke current session",
        security: [{ cookieAuth: [] }],
        responses: {
          200: { description: "Logged out successfully", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
        },
      },
    },
    "/api/users/me": {
      get: {
        tags: ["Users"],
        summary: "Get current user profile",
        security: [{ cookieAuth: [] }],
        responses: {
          200: { description: "Profile retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
        },
      },
      patch: {
        tags: ["Users"],
        summary: "Update current user profile",
        security: [{ cookieAuth: [] }],
        requestBody: {
          content: { "application/json": { schema: { type: "object", properties: { first_name: { type: "string" }, last_name: { type: "string" }, phone: { type: "string" }, address_line: { type: "string" }, city: { type: "string" }, postal_code: { type: "string" }, country: { type: "string" } } } } },
        },
        responses: {
          200: { description: "Profile updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          400: { description: "Validation error" },
        },
      },
    },
    "/api/users": {
      get: {
        tags: ["Users"],
        summary: "Get all users (admin only)",
        security: [{ cookieAuth: [] }],
        responses: {
          200: { description: "Users retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/users/{id}": {
      get: {
        tags: ["Users"],
        summary: "Get user by ID (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "User ID" }],
        responses: {
          200: { description: "User retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
          404: { description: "User not found" },
        },
      },
      delete: {
        tags: ["Users"],
        summary: "Deactivate user (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "User ID" }],
        responses: {
          200: { description: "User deactivated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
          404: { description: "User not found" },
        },
      },
    },
    "/api/users/{id}/role": {
      patch: {
        tags: ["Users"],
        summary: "Update user role (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "User ID" }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", required: ["role"], properties: { role: { type: "string", enum: ["customer", "admin", "manager"] } } } } },
        },
        responses: {
          200: { description: "Role updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/users/{id}/status": {
      patch: {
        tags: ["Users"],
        summary: "Update user active status (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "User ID" }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", required: ["is_active"], properties: { is_active: { type: "boolean" } } } } },
        },
        responses: {
          200: { description: "Status updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/products": {
      get: {
        tags: ["Products"],
        summary: "Get all products (public, paginated)",
        security: [],
        parameters: [
          { in: "query", name: "page", schema: { type: "integer", default: 1 }, description: "Page number" },
          { in: "query", name: "limit", schema: { type: "integer", default: 20 }, description: "Items per page" },
          { in: "query", name: "category_id", schema: { type: "integer" }, description: "Filter by category" },
          { in: "query", name: "subcategory_id", schema: { type: "integer" }, description: "Filter by subcategory" },
          { in: "query", name: "min_price", schema: { type: "number" }, description: "Minimum price filter" },
          { in: "query", name: "max_price", schema: { type: "number" }, description: "Maximum price filter" },
          { in: "query", name: "search", schema: { type: "string" }, description: "Search by title or description" },
          { in: "query", name: "sort_by", schema: { type: "string", enum: ["price", "created_at", "rating_avg", "popularity"] }, description: "Sort field" },
          { in: "query", name: "sort_order", schema: { type: "string", enum: ["asc", "desc"], default: "desc" }, description: "Sort direction" },
        ],
        responses: {
          200: { description: "Products retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
        },
      },
      post: {
        tags: ["Products"],
        summary: "Create a new product (admin only)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "multipart/form-data": { schema: { $ref: "#/components/schemas/ProductInput" } } },
        },
        responses: {
          201: { description: "Product created", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/products/{id}": {
      get: {
        tags: ["Products"],
        summary: "Get product by ID (public)",
        security: [],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Product ID" }],
        responses: {
          200: { description: "Product retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          404: { description: "Product not found" },
        },
      },
      patch: {
        tags: ["Products"],
        summary: "Update product (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Product ID" }],
        requestBody: {
          content: { "multipart/form-data": { schema: { type: "object", properties: { title: { type: "string" }, description: { type: "string" }, price: { type: "number" }, stock: { type: "integer" }, is_active: { type: "string" }, tags: { type: "string" } } } } },
        },
        responses: {
          200: { description: "Product updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
          404: { description: "Product not found" },
        },
      },
      delete: {
        tags: ["Products"],
        summary: "Delete product (admin only, soft-deletes if linked to orders)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Product ID" }],
        responses: {
          200: { description: "Product deleted or deactivated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/products/{productId}/reviews": {
      get: {
        tags: ["Reviews"],
        summary: "Get reviews for a product (public, paginated)",
        security: [],
        parameters: [
          { in: "path", name: "productId", required: true, schema: { type: "integer" }, description: "Product ID" },
          { in: "query", name: "page", schema: { type: "integer", default: 1 } },
          { in: "query", name: "limit", schema: { type: "integer", default: 20 } },
        ],
        responses: {
          200: { description: "Reviews retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
        },
      },
    },
    "/api/categories": {
      get: {
        tags: ["Categories"],
        summary: "Get all categories (public)",
        security: [],
        responses: {
          200: { description: "Categories retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
        },
      },
      post: {
        tags: ["Categories"],
        summary: "Create a category (admin only)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/CategoryInput" } } },
        },
        responses: {
          201: { description: "Category created", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/categories/{id}": {
      get: {
        tags: ["Categories"],
        summary: "Get category by ID (public)",
        security: [],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Category ID" }],
        responses: {
          200: { description: "Category retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          404: { description: "Category not found" },
        },
      },
      patch: {
        tags: ["Categories"],
        summary: "Update category (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Category ID" }],
        requestBody: {
          content: { "application/json": { schema: { $ref: "#/components/schemas/CategoryInput" } } },
        },
        responses: {
          200: { description: "Category updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
      delete: {
        tags: ["Categories"],
        summary: "Delete category (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Category ID" }],
        responses: {
          200: { description: "Category deleted", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/categories/{categoryId}/subcategories": {
      get: {
        tags: ["Subcategories"],
        summary: "Get subcategories by category ID (public)",
        security: [],
        parameters: [{ in: "path", name: "categoryId", required: true, schema: { type: "integer" }, description: "Category ID" }],
        responses: {
          200: { description: "Subcategories retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
        },
      },
    },
    "/api/subcategories": {
      get: {
        tags: ["Subcategories"],
        summary: "Get all subcategories (public)",
        security: [],
        responses: {
          200: { description: "Subcategories retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
        },
      },
      post: {
        tags: ["Subcategories"],
        summary: "Create a subcategory (admin only)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/SubcategoryInput" } } },
        },
        responses: {
          201: { description: "Subcategory created", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/subcategories/{id}": {
      get: {
        tags: ["Subcategories"],
        summary: "Get subcategory by ID (public)",
        security: [],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Subcategory ID" }],
        responses: {
          200: { description: "Subcategory retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          404: { description: "Subcategory not found" },
        },
      },
      patch: {
        tags: ["Subcategories"],
        summary: "Update subcategory (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Subcategory ID" }],
        requestBody: {
          content: { "application/json": { schema: { $ref: "#/components/schemas/SubcategoryInput" } } },
        },
        responses: {
          200: { description: "Subcategory updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
      delete: {
        tags: ["Subcategories"],
        summary: "Delete subcategory (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Subcategory ID" }],
        responses: {
          200: { description: "Subcategory deleted", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/orders": {
      post: {
        tags: ["Orders"],
        summary: "Create a new order (authenticated)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/CreateOrderInput" } } },
        },
        responses: {
          201: { description: "Order created", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
        },
      },
      get: {
        tags: ["Orders"],
        summary: "Get all orders (admin only)",
        security: [{ cookieAuth: [] }],
        responses: {
          200: { description: "Orders retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/orders/my": {
      get: {
        tags: ["Orders"],
        summary: "Get current user's orders (authenticated)",
        security: [{ cookieAuth: [] }],
        responses: {
          200: { description: "Orders retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
        },
      },
    },
    "/api/orders/{id}": {
      get: {
        tags: ["Orders"],
        summary: "Get order by ID (owner or admin)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Order ID" }],
        responses: {
          200: { description: "Order retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          404: { description: "Order not found" },
        },
      },
      delete: {
        tags: ["Orders"],
        summary: "Cancel order (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Order ID" }],
        responses: {
          200: { description: "Order cancelled", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/orders/{id}/status": {
      patch: {
        tags: ["Orders"],
        summary: "Update order status (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Order ID" }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", required: ["status"], properties: { status: { type: "string", enum: ["pending", "processing", "shipped", "delivered", "cancelled", "on_hold"] } } } } },
        },
        responses: {
          200: { description: "Order status updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Invalid status transition" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/reviews": {
      post: {
        tags: ["Reviews"],
        summary: "Add a review (authenticated)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/ReviewInput" } } },
        },
        responses: {
          201: { description: "Review created", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
        },
      },
    },
    "/api/reviews/product/{id}": {
      get: {
        tags: ["Reviews"],
        summary: "Get reviews by product ID (legacy route)",
        security: [],
        parameters: [
          { in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Product ID" },
          { in: "query", name: "page", schema: { type: "integer", default: 1 } },
          { in: "query", name: "limit", schema: { type: "integer", default: 20 } },
        ],
        responses: {
          200: { description: "Reviews retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
        },
      },
    },
    "/api/reviews/{id}": {
      patch: {
        tags: ["Reviews"],
        summary: "Update a review (owner only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Review ID" }],
        requestBody: {
          content: { "application/json": { schema: { type: "object", properties: { rating: { type: "integer", minimum: 1, maximum: 5 }, review_text: { type: "string" } } } } },
        },
        responses: {
          200: { description: "Review updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (not the owner)" },
          404: { description: "Review not found" },
        },
      },
      delete: {
        tags: ["Reviews"],
        summary: "Delete a review (owner only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Review ID" }],
        responses: {
          200: { description: "Review deleted", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (not the owner)" },
        },
      },
    },
    "/api/ml/recalculate-features": {
      post: {
        tags: ["ML"],
        summary: "Trigger user features recalculation (admin only)",
        security: [{ cookieAuth: [] }],
        responses: {
          200: { description: "Recalculation started", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/ml/segments": {
      post: {
        tags: ["ML"],
        summary: "Push batch user segmentation results (admin only)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", required: ["segments"], properties: { segments: { type: "array", items: { $ref: "#/components/schemas/MLSegment" } } } } } },
        },
        responses: {
          200: { description: "Segments updated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/ml/models": {
      post: {
        tags: ["ML"],
        summary: "Register a trained ML model (admin only)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/MLModelRegistration" } } },
        },
        responses: {
          201: { description: "Model registered", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
        },
      },
    },
    "/api/ml/price/predict": {
      post: {
        tags: ["ML"],
        summary: "Predict product price via ML model (admin only)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/PricePredictionInput" } } },
        },
        responses: {
          200: { description: "Price predicted", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
          502: { description: "ML service unavailable" },
        },
      },
    },
    "/api/voice/webhook": {
      post: {
        tags: ["Voice"],
        summary: "Webhook endpoint for voice provider callbacks (HMAC-validated)",
        security: [],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object" } } },
        },
        responses: {
          200: { description: "Webhook processed", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Invalid payload" },
        },
      },
    },
    "/api/voice/initiate/{id}": {
      post: {
        tags: ["Voice"],
        summary: "Initiate a phone confirmation call for an order (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Order ID" }],
        responses: {
          200: { description: "Call initiated", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
          404: { description: "Order not found" },
          409: { description: "Call already in progress" },
        },
      },
    },
    "/api/voice/context/{id}": {
      get: {
        tags: ["Voice"],
        summary: "Get phone confirmation context for an order (admin only)",
        security: [{ cookieAuth: [] }],
        parameters: [{ in: "path", name: "id", required: true, schema: { type: "integer" }, description: "Order ID" }],
        responses: {
          200: { description: "Context retrieved", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires admin role)" },
          404: { description: "No confirmation records found" },
        },
      },
    },
    "/api/chat": {
      post: {
        tags: ["Chat"],
        summary: "Send a chat message (customer only, authenticated)",
        security: [{ cookieAuth: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/ChatInput" } } },
        },
        responses: {
          200: { description: "Message processed", content: { "application/json": { schema: { $ref: "#/components/schemas/ApiResponse" } } } },
          400: { description: "Validation error" },
          401: { description: "Authentication required" },
          403: { description: "Forbidden (requires customer role)" },
        },
      },
    },
  },
};

export const swaggerSpec = swaggerJsdoc({
  definition: swaggerDefinition,
  apis: [],
});
