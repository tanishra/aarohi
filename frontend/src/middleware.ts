import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

// Protect the intake and success routes
export default async function proxy(request: NextRequest) {
  const token = request.cookies.get('aarohi_token');
  const isProtectedRoute = request.nextUrl.pathname.startsWith('/intake') || request.nextUrl.pathname.startsWith('/success');
  const isAuthRoute = request.nextUrl.pathname.startsWith('/login') || request.nextUrl.pathname.startsWith('/register');

  // If no token trying to access protected routes, redirect to login
  if (!token && isProtectedRoute) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // If token exists, verify signature and expiry
  if (token && (isProtectedRoute || isAuthRoute)) {
    try {
      const secret = new TextEncoder().encode(process.env.JWT_SECRET_KEY || '');
      if (!secret.length) {
        return NextResponse.redirect(new URL('/login', request.url));
      }
      await jwtVerify(token.value, secret);
    } catch {
      // Expired, malformed, or forged token — treat as logged out
      const response = NextResponse.redirect(new URL('/login', request.url));
      response.cookies.delete('aarohi_token');
      return response;
    }
  }

  // If user has a valid-looking token and tries to access login or register page
  if (token && isAuthRoute) {
    return NextResponse.redirect(new URL('/intake', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/intake', '/success', '/login', '/register'],
};
