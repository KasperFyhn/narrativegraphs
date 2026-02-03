import { Community, GraphData } from '../types/graph';
import {
  CommunitiesRequest,
  DataBounds,
  GraphFilter,
  GraphQuery,
} from '../types/graphQuery';
import { ConnectionType } from '../hooks/useGraphQuery';

export interface GraphService {
  getConnectionTypes(): Promise<ConnectionType[]>;

  getDataBounds(connectionType: ConnectionType): Promise<DataBounds>;

  getGraph(query: GraphQuery, filter: GraphFilter): Promise<GraphData>;

  findCommunities(
    commRequest: CommunitiesRequest,
    filter?: GraphFilter,
  ): Promise<Community[]>;
}

export class GraphServiceImpl implements GraphService {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async getConnectionTypes(): Promise<ConnectionType[]> {
    return await fetch(`${this.baseUrl}/graph/types`).then((res) => res.json());
  }

  async getDataBounds(connectionType: ConnectionType): Promise<DataBounds> {
    const response = await fetch(
      `${this.baseUrl}/graph/bounds/` + connectionType,
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch data bounds: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      ...data,
      earliestDate: data.earliestDate ? new Date(data.earliestDate) : undefined,
      latestDate: data.latestDate ? new Date(data.latestDate) : undefined,
    };
  }

  async getGraph(query: GraphQuery, filter: GraphFilter): Promise<GraphData> {
    const response = await fetch(`${this.baseUrl}/graph`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...query,
        filter,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch graph: ${response.statusText}`);
    }

    return await response.json();
  }

  async findCommunities(
    commRequest: CommunitiesRequest,
    filter?: GraphFilter | undefined,
  ): Promise<Community[]> {
    const response = await fetch(`${this.baseUrl}/graph/communities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...commRequest,
        graphFilter: filter,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch communities: ${response.statusText}`);
    }

    return await response.json();
  }
}
