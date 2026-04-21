import React, { useState } from 'react';
import { IconSparkles } from './icons/IconSparkles';

interface OTPVerificationProps {
    email: string;
    onVerify: (email: string, otp: string) => Promise<void>;
    onResendOTP: (email: string) => Promise<void>;
    onBack: () => void;
    isLoading: boolean;
    error: string | null;
}

export const OTPVerification: React.FC<OTPVerificationProps> = ({
    email,
    onVerify,
    onResendOTP,
    onBack,
    isLoading,
    error
}) => {
    const [otp, setOtp] = useState('');
    const [resendLoading, setResendLoading] = useState(false);
    const [resendMessage, setResendMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (otp.length === 6) {
            await onVerify(email, otp);
        }
    };

    const handleResend = async () => {
        setResendLoading(true);
        setResendMessage(null);
        try {
            await onResendOTP(email);
            setResendMessage('New OTP sent to your email!');
            setOtp('');
        } catch (err) {
            setResendMessage('Failed to resend OTP. Please try again.');
        } finally {
            setResendLoading(false);
        }
    };

    const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.replace(/\D/g, '').slice(0, 6);
        setOtp(value);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 px-4">
            <div className="max-w-md w-full space-y-8 bg-white dark:bg-gray-800 p-8 rounded-xl shadow-2xl">
                <div className="text-center">
                    <div className="flex justify-center mb-4">
                        <IconSparkles className="w-16 h-16 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                        Verify Your Email
                    </h2>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        We've sent a 6-digit code to
                    </p>
                    <p className="font-medium text-gray-900 dark:text-white">
                        {email}
                    </p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                        </div>
                    )}

                    {resendMessage && (
                        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                            <p className="text-sm text-green-800 dark:text-green-200">{resendMessage}</p>
                        </div>
                    )}

                    <div>
                        <label htmlFor="otp" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Enter OTP
                        </label>
                        <input
                            id="otp"
                            name="otp"
                            type="text"
                            inputMode="numeric"
                            pattern="[0-9]*"
                            autoComplete="one-time-code"
                            required
                            value={otp}
                            onChange={handleOtpChange}
                            maxLength={6}
                            className="appearance-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white dark:bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-center text-2xl tracking-widest font-mono"
                            placeholder="000000"
                        />
                        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
                            Code expires in 5 minutes
                        </p>
                    </div>

                    <div className="space-y-3">
                        <button
                            type="submit"
                            disabled={isLoading || otp.length !== 6}
                            className="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {isLoading ? 'Verifying...' : 'Verify Email'}
                        </button>

                        <div className="flex space-x-3">
                            <button
                                type="button"
                                onClick={handleResend}
                                disabled={resendLoading}
                                className="flex-1 py-2 px-4 border border-indigo-600 text-sm font-medium rounded-lg text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {resendLoading ? 'Sending...' : 'Resend OTP'}
                            </button>

                            <button
                                type="button"
                                onClick={onBack}
                                className="flex-1 py-2 px-4 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                            >
                                Change Email
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
};
