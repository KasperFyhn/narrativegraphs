import { Doc } from '../types/doc';
import { CooccurrenceDetails } from '../types/graph';

export interface CooccurrenceService {
  getDetails(id: string | number): Promise<CooccurrenceDetails>;

  getDocs(id: string | number, limit?: number): Promise<Doc[]>;
}

export class CooccurrenceServiceImpl implements CooccurrenceService {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async getDetails(id: string | number): Promise<CooccurrenceDetails> {
    const response = await fetch(`${this.baseUrl}/cooccurrences/${id}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch entity: ${response.statusText}`);
    }

    return await response.json();
  }

  async getDocs(id: string | number, limit?: number): Promise<Doc[]> {
    const response = await fetch(
      `${this.baseUrl}/cooccurrences/${id}/docs${limit ? '?limit=' + limit : ''}`,
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch doc: ${response.statusText}`);
    }

    return await response.json();
  }
}
