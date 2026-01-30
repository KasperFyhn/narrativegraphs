import React, { createContext, PropsWithChildren, useContext } from 'react';
import { GraphService, GraphServiceImpl } from '../services/GraphService';
import { DocService, DocServiceImpl } from '../services/DocService';
import { EntityService, EntityServiceImpl } from '../services/EntityService';
import {
  RelationService,
  RelationServiceImpl,
} from '../services/RelationService';
import {
  CooccurrenceService,
  CooccurrenceServiceImpl,
} from '../services/CooccurrenceService';

const getApiUrl = (): string => {
  // 1. Check for explicit override (highest priority)
  // Vite uses VITE_ prefix, CRA uses REACT_APP_ prefix
  const envApiUrl = process.env.REACT_APP_API_URL;
  if (envApiUrl) {
    console.log('Using API URL from environment:', envApiUrl);
    return envApiUrl;
  }

  // 2. Localhost development - point to known backend port
  if (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  ) {
    const devApiUrl = 'http://localhost:8001';
    console.log('Detected localhost, using dev API:', devApiUrl);
    return devApiUrl;
  }

  // 3. Production - strip /vis from current URL
  const currentUrl = window.location.href;
  const baseUrl = currentUrl.split('/vis')[0];
  console.log('Using calculated API URL:', baseUrl);
  return baseUrl;
};

interface Services {
  graphService: GraphService;
  docService: DocService;
  entityService: EntityService;
  cooccurrenceService: CooccurrenceService;
  relationService: RelationService;
}

const ServiceContext = createContext<Services | undefined>(undefined);

export const ServiceContextProvider: React.FC<PropsWithChildren> = ({
  children,
}) => {
  // We find the API url dynamically; we know that it will be served
  const apiUrl = getApiUrl();

  const value: Services = {
    graphService: new GraphServiceImpl(apiUrl),
    docService: new DocServiceImpl(apiUrl),
    entityService: new EntityServiceImpl(apiUrl),
    cooccurrenceService: new CooccurrenceServiceImpl(apiUrl),
    relationService: new RelationServiceImpl(apiUrl),
  };

  return (
    <ServiceContext.Provider value={value}>{children}</ServiceContext.Provider>
  );
};

export const useServiceContext = (): Services => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useServiceContext must be used within a ServiceProvider');
  }
  return context;
};
