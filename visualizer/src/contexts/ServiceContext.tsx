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
  const API_URL =
    (window as any).NARRATIVEGRAPHS_CONFIG?.apiUrl || 'http://localhost:8001';

  const value: Services = {
    graphService: new GraphServiceImpl(API_URL),
    docService: new DocServiceImpl(API_URL),
    entityService: new EntityServiceImpl(API_URL),
    cooccurrenceService: new CooccurrenceServiceImpl(API_URL),
    relationService: new RelationServiceImpl(API_URL),
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
