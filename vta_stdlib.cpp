template<long long A, long long B>
struct __add {
    const static long long value = A + B;
};

template<long long A, long long B>
struct __sub {
    const static long long value = A - B;
};

template<long long A, long long B>
struct __div {
    const static long long value = A / B;
};

template<long long A, long long B>
struct __mul {
    const static long long value = A * B;
};

template<long long A, long long B>
struct __mod {
    const static long long value = A % B;
};
