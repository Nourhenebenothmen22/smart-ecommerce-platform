import { Request, Response, NextFunction } from 'express';
import { ZodTypeAny } from 'zod';

/**
 * Interface for the schemas to validate against different request parts.
 */
interface ValidationSchemas {
    body?: ZodTypeAny;
    query?: ZodTypeAny;
    params?: ZodTypeAny;
}

/**
 * Reusable middleware for validating Express request data with Zod.
 *
 * @param schemas Object containing Zod schemas for body, query, and/or params.
 */
export const validate = (schemas: ValidationSchemas) => {
    return async (req: Request, res: Response, next: NextFunction) => {
        try {
            const results = [];

            // Validate req.body
            if (schemas.body) {
                const parsed = await schemas.body.safeParseAsync(req.body);
                if (!parsed.success) {
                    results.push({ part: 'body', errors: parsed.error });
                } else {
                    req.body = parsed.data;
                }
            }

            // Validate req.query
            if (schemas.query) {
                const parsed = await schemas.query.safeParseAsync(req.query);
                if (!parsed.success) {
                    results.push({ part: 'query', errors: parsed.error });
                } else {
                    // Express 5 exposes req.query through a getter-only property.
                    // Keep the parsed query available without assigning to req.query.
                    (req as Request & { validatedQuery?: unknown }).validatedQuery = parsed.data;
                }
            }

            // Validate req.params
            if (schemas.params) {
                const parsed = await schemas.params.safeParseAsync(req.params);
                if (!parsed.success) {
                    results.push({ part: 'params', errors: parsed.error });
                } else {
                    req.params = parsed.data as Record<string, string>;
                }
            }

            // If there are errors, collect them and return 400
            if (results.length > 0) {
                const formattedErrors = results.flatMap(({ part, errors }) =>
                    errors.issues.map((issue) => ({
                        field: issue.path.join('.'),
                        message: issue.message,
                        location: part,
                    }))
                );

                return res.status(400).json({
                    status: 'error',
                    message: 'Validation failed',
                    errors: formattedErrors,
                });
            }

            next();
        } catch (error) {
            next(error);
        }
    };
};
