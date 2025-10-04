import { http, HttpResponse } from 'msw';

export const handlers = [
  // Mock Firebase REST API calls
  http.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword', () => {
    return HttpResponse.json({
      kind: 'identitytoolkit#VerifyPasswordResponse',
      localId: 'mock-user-id',
      email: 'test@example.com',
      displayName: 'Test User',
      idToken: 'mock-id-token',
      registered: true,
      refreshToken: 'mock-refresh-token',
      expiresIn: '3600',
    });
  }),

  http.post('https://identitytoolkit.googleapis.com/v1/accounts:signUp', () => {
    return HttpResponse.json({
      kind: 'identitytoolkit#SignupNewUserResponse',
      localId: 'mock-new-user-id',
      email: 'newuser@example.com',
      displayName: 'New User',
      idToken: 'mock-new-id-token',
      refreshToken: 'mock-new-refresh-token',
      expiresIn: '3600',
    });
  }),

  // Mock Google OAuth
  http.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp', () => {
    return HttpResponse.json({
      kind: 'identitytoolkit#VerifyAssertionResponse',
      localId: 'mock-google-user-id',
      email: 'google@example.com',
      displayName: 'Google User',
      idToken: 'mock-google-id-token',
      refreshToken: 'mock-google-refresh-token',
      expiresIn: '3600',
      photoUrl: 'https://example.com/avatar.jpg',
    });
  }),

  // Mock Firestore REST API
  http.get('https://firestore.googleapis.com/v1/projects/:projectId/databases/(default)/documents/*', ({ request, params }) => {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path.includes('/users/')) {
      return HttpResponse.json({
        name: 'projects/mock-project/databases/(default)/documents/users/mock-user-id',
        fields: {
          id: { stringValue: 'mock-user-id' },
          name: { stringValue: 'Test User' },
          email: { stringValue: 'test@example.com' },
          isOnline: { booleanValue: true },
          lastSeen: { timestampValue: new Date().toISOString() },
        },
        createTime: '2024-01-01T00:00:00Z',
        updateTime: new Date().toISOString(),
      });
    }

    if (path.includes('/locrits/')) {
      return HttpResponse.json({
        name: 'projects/mock-project/databases/(default)/documents/locrits/mock-locrit-id',
        fields: {
          id: { stringValue: 'mock-locrit-id' },
          name: { stringValue: 'Test Locrit' },
          description: { stringValue: 'A test Locrit for testing' },
          ownerId: { stringValue: 'mock-user-id' },
          isOnline: { booleanValue: true },
          lastSeen: { timestampValue: new Date().toISOString() },
        },
        createTime: '2024-01-01T00:00:00Z',
        updateTime: new Date().toISOString(),
      });
    }

    return HttpResponse.json({
      documents: [],
    });
  }),

  http.post('https://firestore.googleapis.com/v1/projects/:projectId/databases/(default)/documents/*', () => {
    return HttpResponse.json({
      name: 'projects/mock-project/databases/(default)/documents/collection/new-doc-id',
      fields: {},
      createTime: new Date().toISOString(),
      updateTime: new Date().toISOString(),
    });
  }),

  // Catch-all handler for unhandled requests
  http.all('*', ({ request }) => {
    console.warn(`Unhandled ${request.method} request to ${request.url}`);
    return HttpResponse.json({ error: 'Not mocked' }, { status: 404 });
  }),
];