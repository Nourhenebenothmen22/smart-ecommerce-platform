import { Request, Response } from 'express';

export class HealthController {
  async check(_req: Request, res: Response) {
    res.status(200).json({
      status: 'success',
      message: 'Server is healthy',
      timestamp: new Date().toISOString(),
    });
  }
}

export const healthController = new HealthController();
