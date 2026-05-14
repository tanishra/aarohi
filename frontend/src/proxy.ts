import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Protect the intake and success routes
export function middleware(request: NextRequest) {
  const token = request.cookies.get('aarohi_token');

  // If user is trying to access protected routes without a token
  if (!token && (request.nextUrl.pathname.startsWith('/intake') || request.nextUrl.pathname.startsWith('/success'))) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // If user is logged in but tries to access login page
  if (token && request.nextUrl.pathname.startsWith('/login')) {
      return NextResponse.redirect(new URL('/intake', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/intake', '/success', '/login'],
};
